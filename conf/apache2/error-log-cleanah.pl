#!/usr/bin/perl -w                                                                 

use strict;

# check we're called with exactly one argument, our output file name               
if ( @ARGV != 1 ) {die "I need exactly one argument <output file>";}

my $in="/dev/stdin";  # we're a filter read from stdin                             
my $out=$ARGV[0];

open (IN,"< $in") or die "Failed to open $in for reading: $! \n";
open (OUT,">> $out") or die "Failed to open $out for writing: $! \n";

# turn on buffer autoflush so tail -f error.log works                              
# (rather than waiting till file handle is closed                                  
my $outf = select(OUT);
$|=1;
select($outf);


# Strip IP's and replace with 0.0.0.0                                              
while (<IN>) {
    s/\[client.*\]/\[client 0.0.0.0\]/;
    print OUT;
}
    close (OUT);
