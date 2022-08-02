import os
import numpy as np
import pickle
import sys
import argparse
from argparse import ArgumentTypeError


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Please give right flag (True or False).')

class Mask_low():

    def __init__(self, depth_file):
        self.depth_file = depth_file
        self.depth_dict = {}
        self.window = args["w"]
        self.lowest_depth = args["d"]
        self.mask_dict = {}
        self.focus_exon = str2bool(args["f"])

    def record_depth(self):
        f = open(self.depth_file)
        for line in f:
            array = line.strip().split()
            gene = array[0]
            depth = int(array[2])
            if gene not in self.depth_dict:
                self.depth_dict[gene] = []
            self.depth_dict[gene].append(depth)

    def get_low_region(self, depth_list, mask_region, interval_start, interval_end):
        
        mask_flag = False
        mask_start, mask_end = 0, 0
        # for i in range(self.window, len(depth_list)):
        for i in range(interval_start+self.window, interval_end):
            win_start = i-self.window
            win_end = i
            win_mean_depth = np.mean(depth_list[win_start:win_end])
            # print (win_mean_depth, self.lowest_depth, mask_flag)
            if win_mean_depth < self.lowest_depth:
                if mask_flag == False:
                    mask_start = win_start
                    mask_end = win_end 
                else:
                    mask_end = win_end
                mask_flag = True
            else:
                if mask_flag == True:
                    if len(mask_region) > 0 and mask_start < mask_region[-1][1]:
                        mask_region[-1][1] = mask_end
                    else:
                        mask_region.append([mask_start, mask_end])
                mask_flag = False
        if mask_flag == True:
            if len(mask_region) > 0 and mask_start < mask_region[-1][1]:
                mask_region[-1][1] = mask_end
            else:
                mask_region.append([mask_start, mask_end])
        return mask_region

    def select_focus_interval(self, depth_list, exon_intervals):
        mask_region = []    
        if self.focus_exon == True:
            for interval in exon_intervals:
                mask_region = self.get_low_region(depth_list, mask_region, interval[0], interval[1])
        else: # full length
            mask_region = self.get_low_region(depth_list, mask_region, 1000, len(depth_list)-1000)
        return mask_region


    def read_exons(self, gene):
        exon_bed = "%s/whole/exon_extent.bed"%(sys.path[0])
        exon_intervals = []
        f = open(exon_bed, 'r')
        for line in f:
            array = line.strip().split()
            if array[0] == gene:
                start = int(array[1])
                end = int(array[2])
                exon_intervals.append([start, end]) 
        f.close()
        return exon_intervals


    def main(self):
        self.record_depth()
        # gene = "HLA_DPB1"
        f = open(mask_bed, 'w')
        mean_depth_dict = {}
        for gene in self.depth_dict.keys():
            depth_list = self.depth_dict[gene]
            mean_depth = np.mean(depth_list[1000:-1000])
            mean_depth_dict[gene] = round(mean_depth)
            exon_intervals = self.read_exons(gene)
            mask_region = self.select_focus_interval(depth_list, exon_intervals)
            # mask_region = self.get_low_region(depth_list)
            # self.mask_dict[gene] = mask_region
            for mask in mask_region:
                print (gene, mask[0]-1, mask[1]-1, file = f)
        f.close()
        print ("Mean depth", mean_depth_dict)
        # print (self.mask_dict)
        # with open("%s/mask_dict.pkl"%(outdir), 'wb') as f:
        #     pickle.dump(self.mask_dict, f)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Mask low-depth regions", add_help=False, \
    usage="%(prog)s -h", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    required.add_argument("-c", type=str, help="depth file generated by samtools depth -a", metavar="\b")
    required.add_argument("-o", type=str, help="outdir", metavar="\b", default="./output")
    optional.add_argument("-w", type=int, help="Windows size while using sliding the ref", metavar="\b", default=20)
    optional.add_argument("-d", type=int, help="Minimum mean depth in a window.", metavar="\b", default=5)
    optional.add_argument("-f", type=str, help="Whether only mask exons.", metavar="\b", default="True")
    optional.add_argument("-h", "--help", action="help")
    args = vars(parser.parse_args()) 

    if len(sys.argv)==1:
        print ("Please use --help to see detail info")
        sys.exit(0)
    # depth_file = "/mnt/d/HLAPro_backup/test_RNA/AMALA_20x/AMALA.realign.sort.depth"
    
    depth_file = args["c"]
    outdir = args["o"]
    mask_bed = "%s/low_depth.bed"%(outdir)
    mas = Mask_low(depth_file)
    mas.main()