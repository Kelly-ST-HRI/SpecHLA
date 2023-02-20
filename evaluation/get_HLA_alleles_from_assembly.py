"""
extract HLA allele from phased assemblies
1. map the HLA database to the assembly
2. obtain the matched length and identity of each allele
3. choose the best allele by balancing the matched length and identity
4. extract the assembly sequence that mapped to the best allele

wangshuai, Feb 20, 2023
"""

import os, re
import pysam


def get_1_element(lst):
    return lst[1]

def get_2_element(lst):
    return lst[2]

def get_3_element(lst):
    return lst[3]

def get_phased_assemblies():
    record_truth_file_dict = {}
    inpath = "/mnt/d/my_HLA/assembly/"
    for file in os.listdir(inpath):
        if file[-5:] != "fasta":
            continue
        sample = file.split("_")[1]
        if sample not in record_truth_file_dict:
            record_truth_file_dict[sample] = ['', '']
        full_file = inpath + file
        if re.search(".h1-", full_file):
            record_truth_file_dict[sample][0] = full_file
        else:
            record_truth_file_dict[sample][1] = full_file
    # print (record_truth_file_dict)
    return  record_truth_file_dict

def change_allele_name(raw, new):
    with open(raw, "r") as infile, open(new, "w") as outfile:
        for line in infile:
            if line.startswith(">"):
                header = line.strip()[1:]
                contig_name = header.split()[1]
                new_header = f">{contig_name}\n"
                outfile.write(new_header)
            else:
                outfile.write(line)

def minimap(sample, hap_index):
    # command = f"{minimap_path} {record_truth_file_dict[sample][hap_index]} {HLA_data}  -o {result_path}/{sample}.h{hap_index+1}.paf -t 10"
    command = f"{minimap_path} {record_truth_file_dict[sample][hap_index]} {HLA_data}  -o {result_path}/{sample}.h{hap_index+1}.sam -a -t 15"
    print (command)
    os.system(command)

def ana_paf(input_paf, gene, sample):
    # Open the PAF file
    align_list = []
    paf_file =  open(input_paf, "r") 
    # Read all lines into a list
    for line in paf_file:
        if not line.startswith(f"{gene}*"):
            continue

        array = line.split("\t")
        matching_bases = int(array[9])
        Alignment_block_length = int(array[10])
        Target_sequence_name = array[5]
        Target_start_position = array[7]
        Target_end_position = array[8]
        identity = round(float(matching_bases)/Alignment_block_length, 6)
        allele = array[0]
        align_list.append([allele, matching_bases, Alignment_block_length, identity, Target_sequence_name, Target_start_position, Target_end_position])
    paf_file.close()
   
    match_sorted_list = sorted(align_list, key=get_1_element, reverse = True)
    identity_sorted_list = sorted(align_list, key=get_3_element, reverse = True)
    print (sample, gene)
    if match_sorted_list[0][0] == identity_sorted_list[0][0]:
        print ("perfect:", match_sorted_list[0])
        select_allele = match_sorted_list[0]
    
    else:
        print ("check to determine use highest identity or match length in person.")
        for allele_info in match_sorted_list[:5]:
            print(allele_info)
        print ("match bases**************************")

        
        for allele_info in identity_sorted_list[:5]:
            print(allele_info)
        print ("identity **************************")

def ana_sam(input_sam, gene, sample):
    # Open the PAF file
    align_list = []
    align_dict = {}
    # # Open the SAM file
    for line in open(input_sam, "r"):
        # Skip header lines
        if line.startswith("@"):
            continue
        if not line.startswith(f"{gene}*"):
            continue
        # print (line)
        align_info = read_sam_line(line)
        align_list.append(align_info)
        align_dict[align_info[0]] = align_info
   
    match_sorted_list = sorted(align_list, key=get_1_element, reverse = True)
    match_sorted_list = resort_list_with_same_alleles(match_sorted_list, 1, 3)
    identity_sorted_list = sorted(align_list, key=get_3_element, reverse = True)
    identity_sorted_list = resort_list_with_same_alleles(identity_sorted_list, 3, 1)
    max_match_len_alleles = get_max_alleles(match_sorted_list, 1)
    max_identity_alleles = get_max_alleles(identity_sorted_list, 3)

    intersection_alleles = list(set(max_match_len_alleles) & set(max_identity_alleles))
    
    print (sample, gene)
    truth_alleles = []
    if sample in truth_1000_dict:
        if gene in truth_1000_dict[sample]:
            truth_alleles = truth_1000_dict[sample][gene]
            # print ("truth", gene, truth_1000_dict[sample][gene])
    print ("truth", truth_alleles)
    if len(intersection_alleles) > 0:
        print ("perfect:", intersection_alleles)
        select_allele = intersection_alleles[0]
        select_allele_list = align_dict[select_allele]
    
    else:
        print ("check to determine use highest identity or match length in person.")
        for allele_info in match_sorted_list[:5]:
            print(allele_info)
        print ("match bases**************************")

        
        for allele_info in identity_sorted_list[:5]:
            print(allele_info)
        print ("identity **************************")
        select_allele_list = compare_match_len_and_identity(match_sorted_list, identity_sorted_list, truth_alleles)
    print (select_allele_list)
    return select_allele_list

def resort_list_with_same_alleles(sorted_list, first_index, second_index):
    flag = True
    while flag:
        flag = False
        new_sorted_list = sorted_list.copy()
        for i in range(len(sorted_list) - 1):
            if sorted_list[i][first_index] == sorted_list[i+1][first_index] and sorted_list[i+1][second_index] > sorted_list[i][second_index]:
                new_sorted_list[i] = sorted_list[i+1]
                new_sorted_list[i+1] = sorted_list[i]
                flag = True
        sorted_list = new_sorted_list.copy()
    # print (sorted_list[:5])
    return sorted_list
    
def get_max_alleles(sorted_list, index):
    max_value = sorted_list[0][index]
    max_allele_list = []
    for list in sorted_list:
        if list[index] == max_value:
            max_allele_list.append(list[0])
        else:
            break
    return max_allele_list

def extract_four_digits(full_name):
    a = full_name.split("*")[1]
    array = a.split(":")
    return array[0] + ":" + array[1]

def compare_match_len_and_identity(match_sorted_list, identity_sorted_list, truth_alleles):
    max_match_len = match_sorted_list[0][1]
    match_len_with_max_identity = identity_sorted_list[0][1]

    max_identity = identity_sorted_list[0][3]
    identiy_with_max_match_len = match_sorted_list[0][3]

    match_len_diff_ratio = (max_match_len - match_len_with_max_identity) / match_len_with_max_identity
    identity_diff_ratio = (max_identity - identiy_with_max_match_len) / identiy_with_max_match_len

    print ("match_len_diff_ratio", match_len_diff_ratio, "identity_diff_ratio", identity_diff_ratio, "1000G truth", truth_alleles)

    if extract_four_digits(match_sorted_list[0][0]) in truth_alleles and extract_four_digits(identity_sorted_list[0][0]) not in truth_alleles:
        select_allele_list = match_sorted_list[0]
    elif extract_four_digits(match_sorted_list[0][0]) not in truth_alleles and extract_four_digits(identity_sorted_list[0][0]) in truth_alleles:
        select_allele_list = identity_sorted_list[0]

    elif identiy_with_max_match_len < 0.999:
        select_allele_list = identity_sorted_list[0]
    elif match_len_diff_ratio < identity_diff_ratio:
        select_allele_list = identity_sorted_list[0]
    elif identity_diff_ratio < 0.005:
        select_allele_list = match_sorted_list[0]
    else:
        print (" no determine")
    
    print ("selected allele is ", select_allele_list[0])
    return select_allele_list
    
def read_1000G_truth():
    truth_1000_dict = {}
    i = 0
    for line in open(truth_1000G_file):
        array = line.strip().split("\t")
        if i == 0 :
            header_list = array
        else:
            sample = array[2]
            truth_1000_dict[sample] = {}
            for j in range(3, 13):
                header = header_list[j]
                gene = header.split("_")[1]
                if gene not in truth_1000_dict[sample]:
                    truth_1000_dict[sample][gene] = []
                # print (sample, j, array)
                typed_allele = array[j]

                truth_1000_dict[sample][gene].append(typed_allele)
        i += 1
    
    return truth_1000_dict

def read_sam_line(line):
    pattern = re.compile(r"(\d+)([MIDNSHP=X])")
    # Split the SAM record into fields
    fields = line.split("\t")

    # Extract the CIGAR string and sequence from the record using regular expressions
    allele_name = fields[0]
    cigar = fields[5]
    sequence = fields[9]
    match_length = 0
    block_length = 0
    target_start = int(fields[3])
    Target_sequence_name = fields[2]


    for length, op in re.findall(pattern, cigar):
        # print (length, op)
        if op == "M":
            match_length += int(length)
        block_length += int(length)

    nm_tag = [tag for tag in fields[11:] if tag.startswith("NM:i:")]
    if len(nm_tag) == 1:
        num_mismatches = int(nm_tag[0].split(":")[2])
    else:
        num_mismatches = 0

    # Calculate the match identity
    match_identity = round(float(match_length-num_mismatches)/block_length, 6)
    target_end = target_start + block_length
    # Print the match length and identity to the console
    # print(cigar, f"{allele_name} Match length: {match_length}, Match identity: {match_identity}", num_mismatches, block_length)
    # break
    return [allele_name, match_length, block_length, match_identity, Target_sequence_name, target_start, target_end]

def extract_seq(select_allele_list, assembly_file, hap_index, sample, gene, out_fasta):

    # open the input FASTA file
    in_fasta = pysam.FastaFile(assembly_file)

    # define the segment name, start position, and end position
    segment_name = select_allele_list[4]
    start_pos = select_allele_list[5] - 1
    end_pos = select_allele_list[6] - 1

    # extract the sequence for the interval
    sequence = in_fasta.fetch(segment_name, start_pos, end_pos)

    # write the segment name and sequence to the output file
    out_fasta.write(f'>{sample}.h{hap_index+1}.HLA-{gene}\t{segment_name}:{start_pos}-{end_pos}\t{select_allele_list[0]}\n{sequence}\n')

    # close the input and output files
    in_fasta.close()
    

if __name__ == "__main__":
    # sample = "HG00096"
    minimap_path = "~/softwares/SpecHLA/bin/minimap2"
    # https://github.com/ANHIG/IMGTHLA/blob/Latest/fasta/hla_gen.fasta
    raw_HLA_data = "/mnt/d/HLAPro_backup/minor_rev/extract_alleles/hla_gen.fasta"
    HLA_data = "/mnt/d/HLAPro_backup/minor_rev/extract_alleles/hla_gen.rename.fasta"
    truth_1000G_file = "/mnt/d/HLAPro_backup/wgs1000/20181129_HLA_types_full_1000_Genomes_Project_panel.txt"
    # change_allele_name(raw_HLA_data, HLA_data)
    result_path = "/mnt/d/HLAPro_backup/minor_rev/extract_alleles/"
    samples_list = ['HG00096', 'HG00171', 'HG00512', 'HG00513', 'HG00514', 'HG00731', 'HG00732', 'HG00733', 'HG00864', 'HG01114', 'HG01505', 'HG01596', 'HG02011', 'HG02492', 'HG02587', 'HG02818', 'HG03009', 'HG03065', 'HG03125', 'HG03371', 'HG03486', 'HG03683', 'HG03732', 'NA12878', 'NA18534', 'NA18939', 'NA19238', 'NA19239', 'NA19240', 'NA19650', 'NA19983', 'NA20509', 'NA20847', 'NA24385']

    record_truth_file_dict = get_phased_assemblies()
    truth_1000_dict = read_1000G_truth()
    # print (record_truth_file_dict.keys())
    # 

    # create an output file for the extracted segment
    out_fasta = open(result_path + "/extracted_HLA_alleles.fasta", 'w')

    for sample in samples_list:
        print (sample)
        for hap_index in range(2):
            # minimap(sample, hap_index)
            # input_paf = f"/mnt/d/HLAPro_backup/minor_rev/extract_alleles/{sample}.h{hap_index+1}.paf"
            input_sam = f"/mnt/d/HLAPro_backup/minor_rev/extract_alleles/{sample}.h{hap_index+1}.sam"
            assembly_file = record_truth_file_dict[sample][hap_index]
            for gene in ["A", "B", "C", "DPA1", "DPB1", "DQA1", "DQB1", "DRB1"]:
                # ana_paf(input_paf, gene, sample)
                select_allele_list = ana_sam(input_sam, gene, sample)
                # print (assembly_file)
                extract_seq(select_allele_list, assembly_file, hap_index, sample, gene, out_fasta)
        #         break
        # break
    out_fasta.close()

    # read_sam()
    # ana_sam(input_sam, gene, sample)