#!/bin/bash

patcher(){
	time=$( date +'%m-%d-%Y-%H,%M,%S')
	mount - / -oremount,rw
	cd /tmp/patch/bash-scripts/patch-files

	chown root:root hello.py
	chmod 755 hello.py
	echo Patching hello.py to /usr/local
	diff -u /usr/local/hello.py hello.py > update.patch
	if [ "$?" = "1" ]; then
		patch --dry-run /usr/local/hello.py < update.patch
		if [ "$?" = "0" ]; then
			patch -b /usr/local/hello.py < update.patch && mkdir -p /tmp/patch/57081_backup_$time && mv /tmp/patch/bash-scripts/patch-files/*.patch /tmp/patch/57081_backup_$time && mv /usr/local/*.orig /tmp/patch/57081_backup_$time
			if [ "$?" = "0" ]; then
				hash1=$(sha1sum $'hello.py' | cut -d ' ' -f 1)
				hash2=$(sha1sum $'/usr/local/hello.py' | cut -d ' ' -f 1)
				if [ "$hash1" == "$hash2" ]; then
					mount - / -oremount,ro
					echo The hash codes of hello.py and /usr/local/hello.py match.
					echo Successfully patched hello.py.
					echo Exiting patching process.
					exit 0
				else
					patch -R /usr/local/hello.py < update.patch
					if [ "$?" = "0" ]; then
						mount - / -oremount,ro
						echo The hash codes of the source file and patch file do not match.
						echo Please check your source and patch files.
						echo Reverting patch and aborting patch process.
						exit 0
					else
						mount - / -oremount,ro
						echo The has codes of the source file and patch file do not match.
						echo Tried to revert patch but it has failed.
						echo Please check your source and patch files.
						echo Aborting patching process.
						exit 1
					fi
				fi
			else
				mount - / -oremount,ro
				echo There was an error during the patching process.
				echo Please double check all back up files for existence.
				echo Please check your source and patch files.
				echo Aborting patching process.
				exit 1
			fi
		else
			mount - / -oremount,ro
			echo There was an error during the dry run process of the patch.
			echo Please check your source and patch files.
			echo Aborting patching process.
			exit 1
		fi
	elif [ "$?" = "0" ]; then
		rm update.patch
		mount - / -oremount,ro
		echo No differences found between source file and patch file.
		echo No patching was initiated.
		echo Aborting patching process.
		exit 1
	elif [ "$?" = "2" ]; then
		mount - / -oremount,ro
		echo An error has occurred during the diff process when creating the update file.
		echo Please check your source file and patch file.
		echo Aborting patching process.
		exit 1
	fi
}
patcher