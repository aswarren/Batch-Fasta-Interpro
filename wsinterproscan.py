#!/usr/bin/env python
# ======================================================================
# WSInterProScan Python client.
#
# Tested with: Python 2.5.1 with SOAPpy 0.11.3
#
# See:
# http://www.ebi.ac.uk/Tools/webservices/services/interproscan
# http://www.ebi.ac.uk/Tools/webservices/clients/interproscan
# http://www.ebi.ac.uk/Tools/webservices/tutorials/python
# ======================================================================
# WSDL URL for service
wsdlUrl = 'http://www.ebi.ac.uk/Tools/webservices/wsdl/WSInterProScan.wsdl'

# Load libraries
import os
import sys
import time
from SOAPpy import WSDL
from optparse import OptionParser

# Usage message
usage = "Usage: %prog [options...] [seqFile]"
# Process command-line options
parser = OptionParser(usage=usage)
parser.add_option('--app', help='List of methods to run')
parser.add_option('--crc', action="store_true", help='Use IprMatches lookup')
parser.add_option('--seqtype', default='P', help='Sequence type')
#parser.add_option('--trlen', type=int, help='Minimum ORF length')
#parser.add_option('--trtable', type=int, help='Translation table to use')
parser.add_option('--goterms', action="store_true", help='Get GO terms')
parser.add_option('-f', '--outformat', help='Output format')
parser.add_option('-a', '--async', action="store_true", help='Async submission')
parser.add_option('--email', help='E-mail address')
parser.add_option('--outfile', help='File name for results')
parser.add_option('--polljob', action="store_true", help='Get job result')
parser.add_option('--status', action="store_true", help='Get job status')
parser.add_option('-j', '--jobid', help='Job Id')
parser.add_option('--trace', action="store_true", help='Show SOAP messages')
parser.add_option('--sequence', help='Input sequence file name')
(options, args) = parser.parse_args()

# Create the service interface
server = WSDL.Proxy(wsdlUrl)

# If required enable SOAP message trace
if options.trace:
	server.soapproxy.config.dumpSOAPOut = 1
	server.soapproxy.config.dumpSOAPIn = 1

# Client-side poll
def clientPoll(jobId):
	result = 'PENDING'
	while result == 'RUNNING' or result == 'PENDING':
		result = server.checkStatus(jobId)
		print >>sys.stderr, result
		if result == 'RUNNING' or result == 'PENDING':
			time.sleep(15)

# Get result for a jobid
def getResult(jobId, count):
	# Check status and wait if necessary
	clientPoll(jobId)
	# Get available result types
	resultTypes = server.getResults(jobId)
	for resultType in resultTypes:
		# Get the result
		result = server.poll(jobId, resultType.type)

		# Derive the filename for the result
		if options.outfile:
			if(',' in options.outfile):
				if(len(options.outfile.split(',')) > count):
					filename = options.outfile.split(',')[count] + '.' + resultType.ext
				else:
					filename = jobId + '.' + resultType.ext
			else:
				filename = options.outfile + '.' + resultType.ext
		else:
			filename = jobId + '.' + resultType.ext
		# Write a result file
		if not options.outformat or options.outformat == resultType.type:
			fh = open(filename, 'w');
			if(type(result)==str):
				fh.write(result)
			fh.close()
			print filename

# Read a file
def readFile(filename):
	fh = open(filename, 'r')
	data = fh.read()
	fh.close()
	return data

#split the seqData into a list of datastructures
def split_fasta(seqData, data_list):
	records=seqData.split('>')# first record should be empty
	if(len(records)==1):
		data_list.append([{'type':'sequence', 'content':records[0]}])
	else:
		for r in records:
			if len(r) > 0:
				data_list.append([{'type':'sequence', 'content':'>'+r}])


data_list=[]
jobid_list=[]


# Get results
if options.polljob and options.jobid:
	getResult(options.jobid)
# Get status
elif options.status and options.jobid:
	status = server.checkStatus(options.jobid)
	print status
# Submit job
elif options.email and not options.jobid:
	if len(args) > 0:
		if os.access(args[0], os.R_OK): # Read file into content
			seqData = readFile(args[0])
			split_fasta(seqData, data_list)
			#content = [{'type':'sequence', 'content':seqData}]
		else: # Argument is a sequence id
			#content = [{'type':'sequence', 'content':args[0]}]
			split_fasta(args[0], data_list)
	elif options.sequence: # Specified via option
		if os.access(options.sequence, os.R_OK): # Read file into content
			seqData = readFile(options.sequence)
			#content = [{'type':'sequence', 'content':seqData}]
			split_fasta(seqData, data_list)
		else: # Argument is a sequence id
			#content = [{'type':'sequence', 'content':options.sequence}]
			split_fasta(options.sequence, data_list)
	iprscan_params = {
		'email':options.email,
		'app':options.app,
		'seqtype':options.seqtype,
		'outformat':options.outformat
		}
	# Booleans need to be represented as 1/0 rather than True/False
	iprscan_params['async'] = 1
	if options.crc:
		iprscan_params['crc'] = 1
	else:
		iprscan_params['crc'] = 0
	if options.goterms:
		iprscan_params['goterms'] = 1
	else:
		iprscan_params['goterms'] = 0
	# Submit the job
	for i in data_list:
		jobid_list.append(server.runInterProScan(params=iprscan_params, content=i))
	if options.async: # Async mode
		print "job_id list: "+' '.join(jobid_list)
	else: # Sync mode
		print "job_id list: "+' '.join(jobid_list)
		time.sleep(5)
		count=0;
		for j in jobid_list:
			getResult(j, count)
			count+=1
else:
	print 'Error: unrecognised argument combination'
	parser.print_help()
