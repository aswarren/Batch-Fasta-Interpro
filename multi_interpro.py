#!/usr/bin/env python
import os, sys, subprocess, getopt #for running bl2seq
from Bio import SeqIO
#This script is for running the winterproscan.py based on a multi-seq fasta file
#Uses biopython and names the output files according to the info in the seq. header

#write out information in fasta format
def write_fasta(header_line, sequence, output_handle):
        fasta_lines = []
        fasta_string= textwrap.fill(sequence, 70)
        fasta_lines.append(header_line)
        fasta_lines.append(fasta_string)
        fasta_lines.append('')
        outstr = '\n'.join(fasta_lines)
        output_handle.write(outstr)

def main(init_args):
	tmp_name="./mg_temp"
	email="example@example.com"
	
	optlist, args=getopt.getopt(init_args, 'i:s:')
	if(len(optlist)<2):# number of independent options
		print "Usage: multi_interpro.py -i [fasta file] -s [script to run]"
		sys.exit()
	for o,v in optlist:
		if(o=='-i'):
			fasta_file=v
		elif(o=='-s'):
			script_file=v
	fasta_handle=open(fasta_file, 'r')
	fasta_records= list(SeqIO.parse(fasta_handle, "fasta"))
	if(len(fasta_records)==0):sys.exit()
	
	i=0
	while i < len(fasta_records):
		j=0
		interpro_out=[]
		tmp_handle=open(tmp_name, 'w')
		while j < 25 and i < len(fasta_records):
			#Normal File naming is based on commented out line below
			#interpro_out.append(fasta_records[i].id.replace('|','_'))
			#Special file naming for missing genes project
			interpro_out.append(fasta_records[i].description.split()[1].split('(')[0])
			SeqIO.write([fasta_records[i]], tmp_handle, "fasta")
			j+=1
			i+=1
		interpro_com=script_file+" --app=all --email="+email+" --sequence="+tmp_name+" --outfile="+','.join(interpro_out)
		print interpro_com
		tmp_handle.close()
		ip=subprocess.Popen([interpro_com], shell=True, close_fds=True)
		ip.wait()

if __name__ == "__main__":
	main(sys.argv[1:])
else:
	print "Running as non-main not supported"
