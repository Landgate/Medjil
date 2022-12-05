#!/usr/bin/env perl

# NAME:
#     verifySub.pl
# PURPOSE:
#     To verfiy that the RINEX files in a submission folder are suitable for
#     submission
# EXPLANATION:
#     The script is run from inside the submission folder. It runs five checks:
# 
#         1) RINEX compliance;
#         2) RINEX version (cannot process version 3.0, yet);
#         3) Observation length (greater than 6 hrs but less than 48 hrs); 
#         4) Sample interval (should be 30 seconds); and
#         5) DOY, i.e., that the DOY in the filename matches the first DOY
#            of the data
# 
#     Files that fail the first check are moved to a sub-directory called
#     'nonComp'. Files that fail the second check can either be moved to a
#     sub-directory (version3) or immediately deleted by invoking the -d
#     switch. Files that fail the third check can either be moved to a
#     sub-directory ('tooShort' or 'tooLong') or immediately deleted by
#     invoking the -d switch. Files that fail the fourth check can either be 
#     moved to a sub-directory 'sample' or immediately deleted by invoking
#     the -d switch. Files that fail the last check can either be moved
#     to a sub-directory 'wrongDOY' or immediately renamed by invoking the -r
#     switch. A log file is created that lists all the files that failed each
#     check.
# 
#     For full verification, the script will need to be run a second time once 
#     the non-compliant RINEX files have been fixed. Before running a second
#     time, the files should be moved from the sub-directories to the archive
#     folder and the sub-directories removed.
# USAGE:
#     verifySub.pl -dr
#     verifySub.pl -h displays the help information
#     verifySub.pl -v displays the version information
# INPUT:
#     There is no input
# OUTPUT:
#     A log file listing all the files that failed each of the checks. Depending
#     on the usage the directory structure and contents are modified
$version = '0.06';
# HISTORY:
#     0.01    2014-08-08  Craig Harrison
#         - Inital version
#     0.02    2014-08-12  Craig Harrison
#         - Added the correct DOY to the log file for those files found to have
#             the incorrect DOY
#     0.03    2014-08-27  Craig Harrison
#         - Added RINEX version 3.0 check
#     0.04    2015-01-14  Craig Harrison
#         - Replaced the UNIX command 'head' with a line read
#     0.05    2015-01-30  Craig Harrison
#         - Removed the code that deletes exisitng directories, such as
#             tooLong or wrongDOY, which can cause inexperienced users to
#             inadvertantly delete their data
#     0.06    2015-03-10  Craig Harrison
#         - Added a sample interval check; must be 30 seconds 

# Load the necessary modules
use File::Copy;
use DateTime::Precise;

# Parse the command line
if ($ARGV[0] eq '-h') {
    &helpInfo;
} elsif ($ARGV[0] eq '-v') {
    &versionInfo;
} elsif ($ARGV[0] eq '-dr' or $ARGV[0] eq '-rd') {
    $delete = $rename = 1;
} elsif ($ARGV[0] eq '-d') {
    $delete = 1;
} elsif ($ARGV[0] eq '-r') {
    $rename = 1;
} elsif ($ARGV[0] eq '-dir') {
    chdir $ARGV[1];
    print "\n### Changing Directory ###\n";
    if (chdir $ARGV[1] eq '1') {
      print "Directory change successful\n";
    }else{
      print "Directory change failed\n";
    }
} elsif ($ARGV[0] eq '') {
    $delete = $rename = 0;
} else {
    print "\n### UNKNOWN COMMAND LINE SWITCH ###\n";
    &helpInfo;
}

# Set some variables
# print 'What is the minimum duration (in hours)? ';
$tooShort = 3600 * 6;
$tooLong = 172800; # 48 hours in seconds

# Open the log file
open LOG, '>verifySub.log';

# Create the directories
mkdir 'nonComp' unless (-d 'nonComp');
mkdir 'version3' unless (-d 'version3');
mkdir 'tooShort' unless (-d 'tooShort');
mkdir 'tooLong' unless (-d 'tooLong');
mkdir 'sample' unless (-d 'sample');
mkdir 'wrongDOY' unless (-d 'wrongDOY');

# Loop over all the RINEX files
$failedCheck1 = $failedCheck2 = $failedCheck3a = $failedCheck3b =
    $failedCheck4 = $failedCheck5 = '';
for $file (glob'*.??[oO]') {
    print "Processing $file...\n";

# Check for RINEX version 3 files
#    open IN, $file;
#    $ver = (split' ', <IN>)[0];
#    close IN;
#    if ($ver eq '3.00') {
#        $failedCheck2 .= "$file\n";

# Depending on the switches either move the file or delete it
#        $delete ? Unlink $file : move $file, version3;
#        next;
#    }

# Run teqc
    $err = $file . '.err';
    @output = `teqc +meta +quiet +err $err $file`;

# If the RINEX file is compliant
    if (@output) {

# Check the observation length
        $length = &getLength(@output);

# If the length is too short        
        if ($length < $tooShort) {
            $length = sprintf '%d', $length;
            $failedCheck3a .= "$file ($length)\n";

# Depending on the switches either move the file or delete it
            $delete ? unlink $file : move $file, tooShort;
            next;
        }
        
# If the length is too long        
        if ($length > $tooLong) {
            $length = sprintf '%d', $length;
            $failedCheck3b .= "$file ($length)\n";

# Depending on the switches either move the file or delete it
            $delete ? unlink $file : move $file, tooLong;
            next;
        }

# Run teqc again to perform the sample interval and DOY check
        @output = `teqc +meta +doy +quiet $file`;

# Sample interval check
        $sample = &getSample(@output);
        if ($sample != 30) {
            $failedCheck4 .= "$file ($sample)\n";

# Depending on the switches either move the file or delete it
            $delete ? unlink $file : move $file, sample;
            next;
        }
            

# DOY check
        $doy1 = substr $file, 4, 3;
        $doy2 = &getDOY(@output);
        ($newFile = $file) =~ s/$doy1/$doy2/;
        if ($doy1 != $doy2) {
            $failedCheck5 .= "$file -> $newFile\n";
            
# Depending on the switches either move the file or rename it
            if ($rename) {
                die "$file can't be renamed $newFile: file already exists\n"
                    if (-e $newFile);
                move $file, $newFile;
            } else {
                move $file, wrongDOY;
            }
        }

# If there is no output then the RINEX file is non-compliant, so move it to the
# sub-directory 'nonComp'
    } else {
        $failedCheck1 .= "$file\n";
        move $file, nonComp;
        move $err, nonComp;
    }    
}    

# Write files that failed any of the checks to the log file
if ($failedCheck1) {
    print LOG "### Non-compliant RINEX files ###\n";
    print LOG $failedCheck1;
}    
if ($failedCheck2) {
    print LOG "### RINEX version 3 files ###\n";
    print LOG $failedCheck2;
}    
if ($failedCheck3a) {
    print LOG "### Too short (<$tooShort) ###\n";
    print LOG $failedCheck3a;
}    
if ($failedCheck3b) {
    print LOG "### Too long (>$tooLong) ###\n";
    print LOG $failedCheck3b;
}    
if ($failedCheck4) {
    print LOG "### Incorrect sampling interval ###\n";
    print LOG $failedCheck4;
}
if ($failedCheck5) {
    print LOG "### Incorrect DOY ###\n";
    print LOG $failedCheck5;
}

# Print to screen the number of RINEX files and the number of stations
for $file (glob'*.??[Oo]') {
    $num1++;
    $station = lc(substr $file, 0, 4);
    $seen{$station}++;
    $num2 = keys %seen;
}    
print "There are $num1 RINEX files and $num2 stations\n";

# Remove the empty error files
unlink glob'*.err';

###############################################################################
# This sub-routine prints the help information
sub helpInfo {
    $prog = (split '/', $0)[-1];
    print "\nUsage:\n\n";
    print "$prog -dr -v -h\n\n";
    print "\t-d\tDelete files that fail the observation length, version, or\n";
    print "\t\t  sample interval check. The default is to move the files to a";
    print "\n\t\t  sub-directory.\n\n";
    print "\t-r\tRename files that fail the DOY check. The default is to\n";
    print "\t\t  move the files to a sub-directory.\n\n";
    print "The above two switches can be combined into one, ";
    print "i.e., -dr or -rd\n\n";
    print "\t-h\tPrint this help information\n";
    print "\t-v\tPrint the version information\n";
    die "\n";
}
###############################################################################
# This sub-routine prints the version information
sub versionInfo {
    $prog = (split '/', $0)[-1];
    print "\n";
    print "$prog v$version\n";
    die "\n";
}
###############################################################################
# This sub-routine calculates the observation length
sub getLength {
    my @output = @_;
    @_ = grep /start date/, @output;
    @_ = split ' ', $_[0];
    $_ = "$_[4] $_[5]";
    my $start = DateTime::Precise->new($_);
    my $offset = $start->gps_seconds_since_epoch;
    @_ = grep /final date/, @output;
    @_ = split ' ', $_[0];
    $_ = "$_[4] $_[5]";
    my $final = DateTime::Precise->new($_);
    my $duration = $final - $start;
    return $duration;
}
###############################################################################
# This sub-routine gets the first DOY of observation
sub getDOY {
    my @output = @_;
    @_ = grep /start date/, @output;
    @_ = split ' ', $_[0];
    my $doy = (split ':', $_[4])[1];
    return $doy
}
###############################################################################
# This sub-routine gets the sample interval
sub getSample {
    my @output = @_;
    @_ = grep /sample interval/, @output;
    my $sample = (split ' ', $_[0])[2];
    return $sample
}
###############################################################################
