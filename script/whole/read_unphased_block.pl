#!/usr/bin/perl -w
use FindBin qw($Bin);
#perl rephase.pl break_points.txt ./ 2 prephase_breakpoints.txt 300 5
my ($bfile, $vdir, $k, $outfile) = @ARGV;

my $db="$Bin/../../db/HLA";
my $bin="$Bin/../../bin";

my $hla_ref="$db/hla.ref.extend.fa";
my $outdir="$vdir/tmp";
`rm -rf $outdir`;
`mkdir $outdir`;
my %hash;
my $count =0;
open IN, "$bfile" or die "$bfile\t$!\n";
<IN>;
while(<IN>){
      chomp;
      my $gen = (split)[0];
      $hash{$gen} .= "$_\n";
      $count += 1;
}
close IN;
#ouput block region
my %hashlen=('HLA_A'=>'3503', 'HLA_B'=>'4081', 'HLA_C'=>'4304', 'HLA_DPA1'=>'9775','HLA_DPB1'=>'11468','HLA_DQA1'=>'6492','HLA_DQB1'=>7480,'HLA_DRB1'=>'11229');
my %hashr;
open OUT, ">$outfile";
my ($ref,$region1,$region2,$break1,$break2,$vcf,$start1,$start2,$end1,$end2,$gene,$n,$score1,$score2);
foreach my $ge(sort keys %hash){
        $gene = $ge;
        my @lines = (split /\n/, $hash{$gene});
        $vcf = "$vdir/"."$gene".".vcf";
        $ref = "$db/whole/$gene";
        `tabix -f $vcf.gz`;
        ($start1,$n) = (1001,0);
        while($n<=$#lines){               
                my @oarrs = (split /\s/, $lines[$n])[0,1,2];
                $break1 = $oarrs[2];
                my $out = join("\t", @oarrs);
                $n += 1;
                if($n>$#lines){ $break2=$hashlen{$gene} + 1000; $n+=1; }
                else{($break2) = (split /\s/, $lines[$n])[2];}
                $end1 = $break1;
                $start2 = $break1 + 1;
                $end2 = $break2;
                #skip the long indel enriched region
                if(($gene eq "HLA_DQB1") && ($break2 >4230) && ($break2 <4600)){$end2 = 4230}
                elsif(($gene eq "HLA_DQB1") && ($break1 < 4230) && ($break2>4230) && ($break2 <4600)){$end2 = 4230}
                elsif(($gene eq "HLA_DQB1") && ($break1 >=4230) && ($break1<4600) && ($break2>4600)){$end1 = 4230; $start2 =4600}
                elsif(($gene eq "HLA_DQB1") && ($break1 < 4230) && ($break2 >4600)){$end1 = 4230; $start2=4600 }
                if(($gene eq "HLA_DRB1") && ($break2 >3950) && ($break2 <4300)){$end2 = 3950}
                elsif(($gene eq "HLA_DRB1") && ($break1 < 3950) && ($break2>3950) && ($break2 <4300)){$end2 = 3950}
                elsif(($gene eq "HLA_DRB1") && ($break1 >=3950) && ($break1<4300) && ($break2>4300)){$end1=3950; $start2 =4300}
                elsif(($gene eq "HLA_DRB1") && ($break1 < 3950) && ($break2>4300)){$end1 = 3950; $start2=4300 }
                $region1 = "$gene".":"."$start1"."-"."$end1";
                $region2 = "$gene".":"."$start2"."-"."$end2";
                $hashr{$region1} = $region2;
                $hashr{$region2} = $region1;
                $start1 = $start2;
       }
}
#return combination of each two hap
foreach my $region1(sort keys %hashr){ 
        foreach my $region2(sort keys %hashr){
                next if($region1 eq $region2);
                for(my $j=1; $j<=$k; $j++){
                     `$bin/samtools faidx $hla_ref $region1 | $bin/bcftools consensus -H $j $vcf.gz | sed  "s/$region1\$/allele$j.break1/" > $outdir/allele$j.break1.fa`;
                     `$bin/samtools faidx $hla_ref $region2 | $bin/bcftools consensus -H $j $vcf.gz | sed  "s/$region2\$/allele$j.break2/" > $outdir/allele$j.break2.fa`;
                }
                `cat $outdir/allele1.break1.fa $outdir/allele1.break2.fa $outdir/allele2.break1.fa $outdir/allele2.break2.fa > $outdir/allele.break.merge.$n.fa`;
                `$bin/blastn -query $outdir/allele.break.merge.$n.fa -out $outdir/allele.break.merge.blast.$n -db $ref -outfmt 7 -max_target_seqs 100 -num_threads 4 -strand plus`;
                 
                
                 open TE, "$outdir/allele.break.merge.blast.$n" or die "blast\t$!\n";
                 my (%hash1,%hash2,%hash11,%hash12,%hash21,%hash22); my ($score1,$score2) = (0,0);
                 while(<TE>){
                      chomp;
                      next if(/^#/);
                      my ($id,$hla,$score) = (split)[0,1,2];
                      if($id eq "allele1.break1"){$hash11{$hla} = $score}
                      if($id eq "allele1.break2"){$hash12{$hla} = $score}
                      if($id eq "allele2.break1"){$hash21{$hla} = $score}
                      if($id eq "allele2.break2"){$hash22{$hla} = $score}
                 }
                 close TE;
                 ##return the score of hap 00/01;
                 my $hhla; my $max = 0;
                 foreach my $hh(sort keys %hash11){
                      my ($s11,$s12,$s21,$s22) = (0,0,0,0);
                      if(exists $hash11{$hh}){$s11 = $hash11{$hh};}
                      if(exists $hash12{$hh}){$s12 = $hash12{$hh};}
                      if(exists $hash21{$hh}){$s21 = $hash21{$hh};}
                      if(exists $hash22{$hh}){$s22 = $hash22{$hh};}
                      my $ss1 = ($s11 + $s12)/2;
                      my $ss2 = ($s21 + $s22)/2;
                      my $rss1 = ($s11 + $s22)/2;
                      my $rss2 = ($s12 + $s21)/2;
                      my ($S1,$S2);
                      if($ss1 >= $ss2){$S1 = $ss1}else{$S1 = $ss2}
                      if($rss1 >= $rss2){$S2 = $rss1}else{$S2 = $rss2}
                      if($S1 >= $max && $S1 >= $S2){
                           $hhla=$hh; $score1 = $S1; $score2 = $S2;
                           $max = $S1; $hash1{$max} .= "\t$score1;$score2;$hhla";
                      }
                      if( $S2 >= $max && $S2 >= $S1){
                           $hhla=$hh; $score2 = $S2; $score1 = $S1;
                           $max = $S2; $hash2{$max} .= "\t$score1;$score2;$hhla";
                      }
                           
       #if($region1 eq "HLA_DRB1:2433-2601" && $region2 eq "HLA_DRB1:2602-3808" ){print "$region1\t$region2\t$hh\t$ss1\t$ss2\t$rss1\t$rss2\t$S1\t$S2\t$score1\t$score2\t$max\n"}

                 }
                 my $out = "";
                 if(exists $hash1{$max}){$out .= $hash1{$max}}
                 if(exists $hash2{$max}){$out .= $hash2{$max}}
                 print OUT "$region1\t$region2\t$out\n";
        }
}                
close OUT;
