set pid [getPID]
set np [getNP]
#set par_list [open "slope_values.txt" r]
set countP 0;


set startT  [clock seconds]

# Getting the list of input motion data
set fp [open "recordData.txt" r]
set content [read $fp]
close $fp
set records [split $content "\n"]

set count 0
set motionFiles {}
set motionDTs {}
set motionNsteps {}
foreach rec $records {
	set element [split $rec " "]
	set colNum 0
	foreach column $element {
		if {$colNum==0} {
			# puts "Column 1: $column"
			lappend motionFiles $column
			set colNum [expr $colNum+1]
		} elseif {$colNum==1} {
			#puts "Column 2: $column"
			lappend motionDTs $column
			set colNum [expr $colNum+1]
		} else {
			# puts "Column 3: $column"
			lappend motionNsteps $column
			set colNum [expr $colNum+1]
			}
	}
	set count [expr $count+1]
}
set numRecords $count
puts "Number of Records: $numRecords"

# set motionSteps [lindex $motionNsteps 1]
# puts "Number of Times Steps: $motionSteps"

set profileList {A B C D}
foreach profile $profileList {
	set prefix Profile
	set suffix .tcl
	set profileName ""
	append profileName $prefix $profile $suffix
# Go through each record and call main script
	for {set rsn 0} {$rsn < $numRecords} {incr rsn 1} {

		if {[expr $countP % $np] == $pid} {

			# Input Velocity file name
			set velocityFile [lindex $motionFiles $rsn]
			puts "Velocity File: $velocityFile"
		
			# Time step increment
			set motionDT [lindex $motionDTs $rsn]
			puts "Motion Timestep: $motionDT"
		
			# Number of time steps
			set motionSteps [lindex $motionNsteps $rsn]
			puts "Number of Timesteps: $motionSteps"
		
			# Motion ID for writing output files
			set motionID [lindex [split $velocityFile .] 0]
			
			source $profileName
			wipe
		}
		incr countP 1
	}
}
set endT    [clock seconds] 

# puts "Total duration for processor $pid [expr $endT-$startT] seconds!"
