#!/bin/bash

#file path
FILEPATH=$(cd `dirname $0`;pwd)

#*****************************************
#Function: BMC Update Tool For Tencent
#auth:     zhong
VERSION=V1R2.2
MODIFY_DATE=20190315
#*****************************************


#*****************************************
str="`date +"%Y%m%d%H%M%S"` "
LOG_DIR="$FILEPATH/update/$str"
LOG_FILE="$LOG_DIR/logAll.log"
RESULT_SUCCESS="$FILEPATH/logs/resultSuccess.txt"
RESULT_FAIL="$FILEPATH/logs/resultFail.txt"
#TMP_FILE="$FILEPATH/tmp/$IP_ADDR.tmp"
HOSTNAME_FILE="$FILEPATH/logs/$IP_ADDR.hostname"
TMP_DIR="$FILEPATH/tmp"
#*****************************************

###########################################
#BMC boot image:0-highVersion,1-image1,2-image2,3-lowVersion,4-newUpgraded,5-notNewUpgraded
BOOT_IMAGE=1
#image to update:0-notCurrent,1-image1,2-image2,3-both
IMAGE_UPDATA=3
#Preserve option:0-preserve all option except sdr ,1-preserve all option,2-preserve no option
PRESERVE_OPTION=0
IP_ADDR=""
USER_NAME=""
USER_PASSWD=""
BIN_FILE=""
USERNAME=""
PASSWORD=""
USERNAMEINIT="root"
PASSWORDINIT="root"
##########################################
BMC_VERSION=""
#Is support type: 0-not support;1-support
SUPPORT="0"
asciiHex=""
CSRFToken=""
cookies=""
PN=""
lan1mac=""
lan8mac=""
lan_ded=""

#retry times
retrytimes=3
##########################################
#preserve option
sdr=0
fru=1
sel=1
ipmi=1
pef=1
sol=1
smtp=1
user=1
dcmi=1
network=1
ntp=1
snmp=1
ssh=1
kvm=1
authentication=1
syslog=1
hostname=1
############################################

#######Thread set#############################
THREAD_MAX=200
THREAD_NUM=20
STOP_FILE="$FILEPATH/batchstop"
###########################################

function printHelp()
{
    echo "Usage:    ./bmc_update.sh [cmd] [param]"
    echo "    cmd: "
    echo "        -s      Single BMC Update"
    echo "        -b      Batch  BMC Update"
    echo "        -box    SF0224P1/BX512-IP Update BOX BMC through Host BMC"
    echo "        -stop   stop batch BMC update"
    echo "    param:"
    echo "        Reference different cmd"
    echo
    
    echo "Single BMC Usage(-s): ./bmc_update.sh -s ip username password fwfile [PRESERVE_OPTION] [IMAGE_UPDATA] [BOOT_IMAGE]"
    echo "       ip                     BMC ipaddress"
    echo "       username               BMC user name"
    echo "       password               BMC user password"
    echo "       binfile                BMC upgrade bin file"
    echo "       PRESERVE_OPTION        optional(default:0)  BMC upgrade preserve option:  1-preserve all options ; 0-not preserve sdr options 2-preserve no option."
    echo "       IMAGE_UPDATA           optional(default:3)  the image to upgrade:  0-notCurrent,1-image1,2-image2,3-both"
    echo "       BOOT_IMAGE             optional(default:1)  BMC boot image:   0-highVersion,1-image1,2-image2,3-lowVersion,4-newUpgraded,5-notNewUpgraded"

    echo "example:   ./bmc_update.sh -s 100.2.2.2 root root bmc.bin 1 1 1"
    echo 
    echo 
    echo "Batch BMC Update Usage(-b): ./bmc_update.sh -b configfile"
    echo "configFile format：ip,username,password,fwfile,PRESERVE_OPTION,IMAGE_UPDATA,BOOT_IMAGE"
    echo "       ip                     BMC ipaddress"
    echo "       username               BMC user name"
    echo "       password               BMC user password"
    echo "       binfile                BMC upgrade bin file"
    echo "       PRESERVE_OPTION        optional(default:0)  BMC upgrade preserve option:  1-preserve all options ; 0-not preserve sdr options 2-preserve no option."
    echo "       IMAGE_UPDATA           optional(default:3)  the image to upgrade:  0-notCurrent,1-image1,2-image2,3-both"
    echo "       BOOT_IMAGE             optional(default:1)  BMC boot image:   0-highVersion,1-image1,2-image2,3-lowVersion,4-newUpgraded,5-notNewUpgraded"
    echo
    echo
    
    echo "SF0224P1/BX512-IP Update BOX BMC through Host BMC (-box):  ./bmc_update.sh -box ip username password binfile"
    echo "       ip                     Host BMC ipaddress"
    echo "       username               Host BMC user name"
    echo "       password               Host BMC user password"
    echo "       binfile                Box BMC upgrade bin file"

    echo " example    ./bmc_update.sh -box 100.2.2.2 root root tflex_box.bin"                        
                                    
}

function printToolVersion()
{
    recordLog 2 "BMC Update Tool version is $VERSION , modify date is $MODIFY_DATE" "Start"
}

function waitz()
{
	for((i=0;i<=8;i++))
	do
		ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc info |grep "Provides Device SDRs " >/dev/null 2>&1
		if [ $? = 0 ] ;then	
			recordLog  "$IP_ADDR BMC is Active, with user:$USER_NAME, pass:$USER_PASSWD "
			return 0
		else
			recordLog  "$IP_ADDR BMC is not Active , with user:$USER_NAME, pass:$USER_PASSWD, wait... "
			sleep 10
		fi
	done
	
	
	#check active use root root
	for((i=0;i<=3;i++))
	do
		ipmitool -I lanplus -H $IP_ADDR -U $USERNAMEINIT -P $PASSWORDINIT mc info |grep "Provides Device SDRs " >/dev/null 2>&1
		if [ $? = 0 ] ;then				
			USER_NAME=$USERNAMEINIT
			USER_PASSWD=$PASSWORDINIT
			recordLog  "$IP_ADDR BMC is Active, with init user:$USER_NAME, pass:$USER_PASSWD "
			sleep 1
			return 0
		else
			recordLog  "$IP_ADDR BMC is not Active , with init user:$USERNAMEINIT, pass:$PASSWORDINIT, wait... "
			sleep 10
		fi
	done
	recordLog "$IP_ADDR: Update Stopped. BMC not response, please check user: $USER_NAME, pass:$USER_PASSWD and root/root" "Failed"
	return 1
}

function exce_ipmi()
{
	if [ ! -d "$TMP_DIR" ]; then  
		mkdir -p $TMP_DIR
	fi 
	
	if [ -e $TMP_FILE ]
	then
		rm $TMP_FILE
	fi
	
	waitz $IP_ADDR
	if [ $? -ne 0 ] ;then
	    return 255
	fi

	for((i=0;i<=2;i++))
	do
		ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD $1 > $TMP_FILE  2>&1 
		if [ $? = 0 ] ;then	
			tmp=`cat $TMP_FILE | grep Unable`
			if [ $tmp -z ]
			then
				#recordLog 2  "cmd execute OK: $1 " 
				return 0
			else
				cat $tmp
			fi		
		else
			recordLog 2  "$IP_ADDR:cmd execute failed:$1 "
		fi
		sleep 5
	done
	echo "$IP_ADDR: IPMI cmd-$1- execute err, Stop to update !!!!"
	return 1
}

function recordLog()
{
    note=`echo $2|sed -r 's/"//g'`
	if [ "$1" == "1" ]
	then
		echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
	elif [ "$1" == "2" ]
	then
		echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
		echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
	elif [ "$1" == "3" ]
	then
	    #success log file
	    echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
		#echo "`date` $2" >> $RESULT_SUCCESS
	elif [ "$1" == "4" ]
	then
	    # failure log
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
    elif [ "$1" == "5" ]
	then
	    # 
        echo -ne "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
        echo -ne "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
	else
		return ;	
	fi	
}

#stop batch update
function stopBatch(){
    if [ ! -e "$STOP_FILE" ]
    then
        touch $STOP_FILE
        recordLog 2  "stop batch update,STOP_FILE:$STOP_FILE"
    fi
}

dec2hex(){
    printf "%x" $1
}
hex2dec(){
    printf "%d" $1
}

toasciihex(){
    asciiHex=""
    STR=$1
    len=${#STR}
    for ((i=1;i<=len;i++))
    do
        a=${STR:i-1:1}
        b=`echo $a |tr -d "\n"|od -An -t dC`
        c=$[$b^127]
        d=$(dec2hex $c)
        if [[ $i -lt $len ]];then 
            asciiHex="${asciiHex}${d}-"
        else
            asciiHex="${asciiHex}$d"
        fi
    done
return 0
}

function getfwversion()
{
    #get BMC Version
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0x37 0x00  2>&1`
    if [ $? -ne 0 ]
	then
		#recordLog 2 "${IP_ADDR}: Get BMC Version Failed!" "Start"
		return 255
	fi
	verison1=`echo ${res} | awk -F ' ' '{print $3}'`
	verison2=`echo ${res} | awk -F ' ' '{print $4}'`
	verison3=`echo ${res} | awk -F ' ' '{print $5}'`
	BMC_VERSION=`printf "%d.%d.%d" 0x0${verison1} 0x0${verison2} 0x0${verison3}`
	recordLog 2 "${IP_ADDR}  Current BMC Version: ${BMC_VERSION}" ""  ""
}

function  checkFruPS()
{
    #get hostName
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x32 0x6b 0x01 0x00 2>&1`
    lenHost=`echo $res | awk -F ' ' '{print $'$2'}'`
    lenHost = hex2dec $lenHost
    i=0
	while [ $i -lt $lenHost ]
	do	
		arry[$i]=`echo $res | awk -F ' ' '{print $'$(i+2)'}'`
		let i++
	done
	
	res=`cat $TMP_FILE | grep "Product Serial" | head -1 | awk -F ' ' '{print $4}'`
	recordLog 2 "$IP_ADDR: Check Product Serial, bmc_product_serial=$res" "Start" "Upload File"
	
	
    #get Product Serial
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD fru  2>&1 | grep "Product Serial" | head -1 | awk -F ' ' '{print $4}'`
	recordLog 2 "$IP_ADDR: Check Product Serial, bmc_product_serial=$res" "Start" "Upload File"
	
	# IP Address Source
	res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 1  2>&1 | grep "IP Address Source" | head -1 | awk -F ' ' '{print $5}'`
	recordLog 2 "$IP_ADDR: Check bmc ip mode, bmc_ip_address_mode=$res" "Start" "Upload File"
	
}

checkfwversion()
{
    ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc info  2>&1
	if [ $? -ne 0 ]
	then
		return 255
	fi
	version=`cat $TMP_FILE | grep 'Firmware Revision'`
	if [ $# -eq 0 ]
	then 
		echo "$IP_ADDR: $version"
		echo "$IP_ADDR: $version" >> $LOG_FILE
		return 0
	fi

	echo "$IP_ADDR: Check version if $1 " >> $LOG_FILE
	echo "$IP_ADDR: Check version if $1 "
	if [[ $version =~ $1 ]]
	then
		echo "$IP_ADDR: Current $version"
		echo "$IP_ADDR: Current $version" >> $LOG_FILE
		return 0
	elif [[ $version =~ $2 ]]
	then
		echo "$IP_ADDR: Current $version"
		echo "$IP_ADDR: Current $version" >> $LOG_FILE
		return 0
	else
		echo "$IP_ADDR: Current $version !!!!"
		echo "$IP_ADDR: Current $version !!!!" >> $LOG_FILE
		return 1
	fi
}
PNLIST=(NF5280M5,SA5212M5,NF5180M5,SA5112M5,NF5468M5,NF5468M5-S,NF5468M5-P,NF5468M5S,SF0224P1,BX512-IP,SA5214M5,NF8260M5,SA8212M5)
function check_productName_fru()
{
    PN=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD fru 2>&1 | grep " Product Name" | head -1 | awk -F ' ' '{print $4}'`
    
    if echo "${PNLIST[@]}" | grep -w "$PN" &>/dev/null; then
        recordLog 2 "$IP_ADDR Product Name is $PN" "Start" "Upload File"
        SUPPORT="1"
        return 0
    else
        recordLog 2 "$IP_ADDR Product Name $PN" "Start" "Upload File"
        SUPPORT="0"
        return 255
    fi
}

function delete_session()
{
	res=`curl -s -X DELETE -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken"  https://$IP_ADDR/api/session --insecure`
	if [ $? -ne 0 ]
	then
		return 255
	fi
	rm $TMP_DIR/cookies_$IP_ADDR
	recordLog 2 "close session:$res" "Finish" "Activate"
	
}
function get_update_progress()
{
	res=`curl -s -X GET -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" https://$IP_ADDR/api/maintenance/firmware/flash-progress --insecure`
	progress=`echo $res | awk -F 'progress' '{print $2}' | awk -F '\"' '{print $3}'`
	if [ $? -ne 0 ]
	then
		return 255
	fi

	if [ "$progress" == "Complete..." ] || [ "$progress" == "Completed." ] || [ "$progress" == "completed." ] || [ "$progress" == "Success..." ]
	then
		let progress=100
		recordLog 3 "$IP_ADDR: BMC update:${progress} %" "In Progress" "Apply"
		recordLog 2 "$IP_ADDR: Update success,bmc will auto restart!" "Finish" "Apply"
		break
	else
	    progress=`echo $progress | awk -F '%' '{print $1}'`
	fi
	progressState=`echo $res | awk -F 'state' '{print $2}' |awk -F ":" '{print $2}' |awk -F "}" '{print $1}'`
	if [ "$progressState" == " 2 " ]
    then
    	let progress=100
    fi
    #check progress number
    echo $progress |grep "^[[:digit:]]\+$" >>/dev/null
    if [ $? -ne 0 ]
    then
        echo "progress is:$progress"
        sleep 100
        return 100
    fi
    if [ $progress -eq 100 ]
	then
    	if [ "$progressState" == " 2 " ]
    	then
    		let progress=100
    	else
    	    let progress=99
    	fi
    fi
    return $progress
}

function flash_node()
{	
	updateFailTime=0
	while [ 1 ]
	do 
	    load_and_update $IP_ADDR $USER_NAME $USER_PASSWD $BIN_FILE
	    if [ $? -ne 0 ]
		then
			sleep 900
			let updateFailTime=updateFailTime+1
			recordLog 2 "$IP_ADDR: Update Progress failed with retry $updateFailTime times" "Failed"
			
			if [ $updateFailTime -ge $retrytimes ]
			then
				recordLog 2 "$IP_ADDR: Update Progress failed with retry $updateFailTime times" "Failed"
				return 255
			fi	
	    else
			#recordLog 2 "$IP_ADDR: Update Progress Sucess" "Success"
			break;
		fi
    done
    
	lastProgress=0
    loopNum=0
    loopMax=100
    errorNum=0
    errorMax=5
	while [ 1 ]
	do
		get_update_progress
		PROGRESS=$?
		if [ $PROGRESS -le 100 ]
		then
		    let lastProgress=$PROGRESS
		    recordLog 3 "$IP_ADDR: BMC update:${PROGRESS} %" "In Progress" "Apply"
			if [ $PROGRESS -eq 100 ]
			then
				recordLog 2 "$IP_ADDR: Update success, bmc will auto restart!" "Finish" "Apply"
				break
			fi
		else
		    if [ $lastProgress -ge 60 ]
			then
			    recordLog 2 "$IP_ADDR: Update success, bmc will auto restart!" "Finish" "Apply"
				break
			fi
			errorNum=$(($errorNum + 1 ))
            if [ $errorNum -gt $errorMax ]
            then
                recordLog 2 "$IP_ADDR BIOS maybe update success $errorNum !" "Finish" "Apply"
                break
            fi
		fi
		sleep 5
		loopNum=$(($loopNum + 1 ))
        if [ $loopNum -gt $loopMax ]
        then
            recordLog 2 "$IP_ADDR BIOS maybe update success $loopNum timeout!" "Finish" "Apply"
            break
        fi
	done
	sleep 150
	recordLog 2  "$IP_ADDR: Update finish to check active"  "Finish" "Apply"
	waitz $IP_ADDR
	if [ $? -ne 0 ]
	then
		recordLog 2  "$IP_ADDR: Update finish to check active failed" "Finish" "Apply"
		return 255
	fi 
	return 0
}
#
function load_and_update()
{
	toasciihex $USER_NAME
	USERNAME=$asciiHex
	toasciihex $USER_PASSWD
	PASSWORD=$asciiHex
	#admin=1e-1b-12-16-11
	let FAIL_COUNT=0
	for ((i=1; i<=$retrytimes; i++))
    do
    	webres=`curl -s --cookie-jar $TMP_DIR/cookies_$IP_ADDR  -X POST  --data "username=$USERNAME&password=$PASSWORD&encrypt_flag=1" https://$IP_ADDR/api/session --insecure`
    	result=`echo $webres|grep "error"`
    	if [ "$result" != "" ]
        then
            let FAIL_COUNT++
            sleep 10
            continue
        fi
        CSRFToken=`echo "$webres"|awk -F "CSRFToken" '{print $2}' |awk -F '"' '{print $3}'`
        #cookies=`cat cookies|grep  QSESSIONID |awk -F "QSESSIONID" '{print $2}'| sed 's/^[ \t]*//g'`
        if [[ "$CSRFToken"x == ""x  ]]
        then
            let FAIL_COUNT++
            sleep 10
        else
            recordLog 2 "$IP_ADDR: Success to create session" "In Progress" "Upload File"
            break
        fi
        #echo "CSRFToken:$CSRFToken"
        #echo "cookies:$cookies"
    done
    if [ $FAIL_COUNT -eq $retrytimes ];then
        recordLog 2  "$IP_ADDR: Failed to get session,detail: $webres" "In Progress" "Upload File"
        return 255
    fi
    
	
    #进行双镜像设置
    recordLog 2 "$IP_ADDR: Begin to set dual image config ,boot image:$BOOT_IMAGE......" "In Progress" "Upload File"
    setimage=`curl -s -X PUT -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"boot_image":"'$BOOT_IMAGE'"}'  https://$IP_ADDR/api/maintenance/dual_image_config --insecure`
    result=`echo $setimage|grep "error"`
	if [[ "$result" != "" || "$setimage"x == ""x ]]
    then
    	recordLog 2  "$IP_ADDR: Failed to set dual image config,detail: $setimage" "In Progress" "Upload File"
    	delete_session
    	return 255
    fi
    recordLog 2 "$IP_ADDR: End to set dual image config:$setimage" "In Progress" "Upload File"
    
	#保留配置选项
	preserve_option_start=`curl -s -X GET -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json"   https://$IP_ADDR/api/maintenance/preserve --insecure`
	recordLog 2 "$IP_ADDR: Before set preserve option:$preserve_option_start" "Start"
	recordLog 2 "$IP_ADDR: Begin to set preserve configure......" "Start"
	preserve=`curl -s -X PUT -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"sdr":"'$sdr'","fru":"'$fru'","sel":"'$sel'","ipmi":"'$ipmi'","pef":"'$pef'","sol":"'$sol'","smtp":"'$smtp'","user":"'$user'","dcmi":"'$dcmi'","network":"'$network'","ntp":"'$ntp'","snmp":"'$snmp'","ssh":"'$ssh'","kvm":"'$kvm'","authentication":"'$authentication'","syslog":"'$syslog'","hostname":"'$hostname'"}'  https://$IP_ADDR/api/maintenance/preserve --insecure`
	result=`echo $preserve|grep "error"`
	if [ "$result" != "" ]
    then
    	recordLog 2  "$IP_ADDR: Failed to set preserve configure,detail: $preserve" "In Progress" "Upload File"
    	delete_session
    	return 255
    fi
	recordLog 2 "$IP_ADDR: End to set preserve configure,result:$preserve" "In Progress" "Upload File"
	preserve_option_end=`curl -s -X GET -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json"   https://$IP_ADDR/api/maintenance/preserve --insecure`
	recordLog 2 "$IP_ADDR: After set preserve option:$preserve_option_end" "Start"
	
	#optionUser=`echo $preserve_option_end |grep user | awk -F"user" '{print $2}'|awk -F"," '{print $1}'|awk -F": " '{print $2}'`

	
	
	#设置要更新的镜像
	recordLog 2 "$IP_ADDR: Begin to set flash_image_config ,the image to update is:$IMAGE_UPDATA ......" "In Progress" "Upload File"
	flashImage=`curl -s -X PUT -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"image_update":"'$IMAGE_UPDATA'","reboot_bmc":"1"}'  https://$IP_ADDR/api/maintenance/flash_image_config --insecure`
	result=`echo $flashImage|grep "error"`
	if [ "$result" != "" ]
    then
    	recordLog 2  "$IP_ADDR: Failed to set flash_image_config,detail: $flashImage" "In Progress" "Upload File"
    	if [ "$PN" != "SA5214M5" ]
        then
    	    delete_session
    	    return 255
    	fi
    fi
	recordLog 2 "$IP_ADDR: Flash_image_config:$flashImage" "In Progress" "Upload File"
	
	
	imageConfig=`curl -s -X GET -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken"   https://$IP_ADDR/api/maintenance/dual_image_config --insecure`
	recordLog 2 "$IP_ADDR: Dual_image_config result:$imageConfig" "In Progress" "Upload File"
	
	#进入升级模式
	recordLog 2 "$IP_ADDR: Begin to into flash mode......" "In Progress" "Upload File"
	flashMode=`curl -s -X PUT -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json"  https://$IP_ADDR/api/maintenance/flash --insecure`
	result=`echo $flashMode|grep "error"`
	if [ "$result" != "" ]
    then
    	recordLog 2  "$IP_ADDR: Failed to into flash mode,detail: $flashMode" "In Progress" "Upload File"
    	delete_session
    	return 255
    fi
	recordLog 2 "$IP_ADDR: End to into flash mode,result:$flashMode" "In Progress" "Upload File"
	
	#上传升级镜像
	recordLog 2 "$IP_ADDR: Begin to in upload image file:$BIN_FILE,please wait......" "Upload File"
	firmware=`curl -s -X POST -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -F "fwimage=@$BIN_FILE;filename=$BIN_FILE;"  https://$IP_ADDR/api/maintenance/firmware --insecure`
	result=`echo $firmware|grep "error"`
	if [[ "$result" != ""  || "$firmware"x == ""x ]]
    then
    	recordLog 2 "$IP_ADDR: Failed to upload image file,detail: $firmware" "In Progress" "Upload File"
    	return 255
    fi
	recordLog 2 "$IP_ADDR: Success to upload image file:$BIN_FILE,result:$firmware" "In Progress" "Upload File"
	
	#检查镜像
	recordLog 2 "$IP_ADDR: Begin to in verification image file:$BIN_FILE,please wait......" "In Progress"  "File Vertify"
	verification=`curl -s -X GET -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json"  https://$IP_ADDR/api/maintenance/firmware/verification --insecure`
	result=`echo $verification|grep "error"`
	if [[ "$result" != "" || "$verification"x == ""x ]]
    then
    	recordLog 2  "$IP_ADDR: Failed to verification image file,please check image file:$BIN_FILE, detail: $verification" "In Progress"  "File Vertify"
    	return 255
    fi
	recordLog 2 "$IP_ADDR: Verification:$verification" "In Progress"  "File Vertify"
	recordLog 2 "$IP_ADDR: Success to verification image file" "In Progress"  "File Vertify"
	
	
	#升级镜像
	recordLog 2 "$IP_ADDR: Begin to upgrade bmc ,PRESERVE_OPTION:$PRESERVE_OPTION ......" "In Progress" "Apply"
	upgrade=`curl -s -X PUT -b $TMP_DIR/cookies_$IP_ADDR -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type: application/json;charset=UTF-8" --data '{"preserve_config":"'$PRESERVE_OPTION'","flash_status":"1"}'  https://$IP_ADDR/api/maintenance/firmware/upgrade --insecure`
	result=`echo $upgrade|grep "error"`
	if [ "$result" != "" ]
    then
    	recordLog 2  "$IP_ADDR: Failed to upgrade,detail: $upgrade" "" "Apply"
    	return 255
    fi
	recordLog 2 "$IP_ADDR: BMC upgrade configure:$upgrade" "In Progress" "Apply"
}


checklan8ip()
{
    lan8ip=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 8 2>&1| grep "IP Address" |awk -F" : " '{print $2}' | grep -v "Address"`
	if [ "$lan8ip" == "$IP_ADDR" ]
	then
		recordLog 2 "$IP_ADDR: Given ip is sharenic: $lan8ip" "In Progress" "Upload File"
		return 0
	else
		recordLog 2 "$IP_ADDR: Given ip is Dedicated  " "In Progress" "Upload File"
		return 1
	fi
}
function check_mac_get()
{
	if [ $# -ne 6 ]
	then
		recordLog 2 "$IP_ADDR: Check_mac params error with $# not 6!!" "In Progress" "Upload File"
		return 0;
	fi	
	if [ $1 == "6c" -a $2 == "92" -a  $3 == "bf" ]
	then
	  if [ $4 == "00" -a $5 == "00" -a $6 == "00" ]
	  then
	    recordLog 2 "$IP_ADDR: Get bad mac address 0!!" "In Progress" "Upload File"
	    return 0;
	  fi
	  recordLog 2 "$IP_ADDR: Get mac address is ok!" "In Progress" "Upload File"
	  return 1;
	else
	  recordLog 2 "$IP_ADDR: Get bad mac address 1!!" "In Progress" "Upload File"
	  return 0;
	fi		
}

function check_mac_set()
{
	if [ $1 == "6c" -a $2 == "92" -a  $3 == "bf" ]
	then
	  if [ $4 == "00" -a $5 == "00" -a $6 == "00" ]
	  then
	    recordLog 2 "$IP_ADDR: bad mac address when set 0, stop update!!" "In Progress" "Upload File"
	    return 1;
	  fi
	  echo "mac address is ok!" 
	  return 0;
	else
	  recordLog 2 "$IP_ADDR: mac address is $1 $2 $3 $4 $5 $6" "In Progress" "Upload File"
	  return 0;
	fi		
}

function flashmac()
{
if [ $# -ne 7 ]
then
	return 255
else
	if [ $1 -eq 0 ]
	then
	    #专有网口
        #recordLog 2 "$IP_ADDR: ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0x11 0x01 0x06 0x08 0x00 0x$2 0x$3 0x$4 0x$5 0x$6 0x$7" "Start"
        ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0x11 0x01 0x06 0x08 0x00 0x$2 0x$3 0x$4 0x$5 0x$6 0x$7 2>&1
		if [ $? -ne 0 ]
    	then
    		recordLog 2  "$IP_ADDR: Set mac address failed,stop update" "In Progress" "Upload File"
    		return 255
    	fi
		sleep 3
		lan1new=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 1 2>&1 | grep "MAC Address"`
		if [ $? -ne 0 ]
    	then
    		return 255
    	fi
		echo "lan 1:$lan1new"
		return 0
	fi
	if [ $1 -eq 1 ]
	then
		recordLog 2 "$IP_ADDR: flash lan 8 MAC" "In Progress" "Upload File"
		recordLog 2 "$IP_ADDR: ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x0c 0x01 0x08 0xc2 0x01 " "In Progress" "Upload File"
		ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x0c 0x01 0x08 0xc2 0x00 2>&1
		if [ $? -ne 0 ]
    	then
    		return 255
    	fi
		sleep 1
		recordLog 2 "$IP_ADDR: ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x0c 0x01 0x08 0x05 0x$2 0x$3 0x$4 0x$5 0x$6 0x$7 " "In Progress" "Upload File"
		ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x0c 0x01 0x08 0x05 0x$2 0x$3 0x$4 0x$5 0x$6 0x$7 2>&1
		if [ $? -ne 0 ]
    	then
    		return 255
    	fi
		sleep 1
		return 0
	fi
	return 255	
fi 
}

function lanmac_get()
{
    lan1mac=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 1 2>&1 | grep "MAC Address" | head -1 | awk -F" :" '{print $2}'`
    recordLog 2 "$IP_ADDR: lan print 1 Dedicated MAC : $lan1mac" "In Progress" "Upload File"
     
    mac1=`echo $lan1mac|cut -d ":" -f1`  
    mac2=`echo $lan1mac|cut -d ":" -f2`
    mac3=`echo $lan1mac|cut -d ":" -f3`
    mac4=`echo $lan1mac|cut -d ":" -f4`
    mac5=`echo $lan1mac|cut -d ":" -f5`
    mac6=`echo $lan1mac|cut -d ":" -f6`
    check_mac_get $mac1 $mac2 $mac3 $mac4 $mac5 $mac6 ;
    
	
    lan8mac=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 8 2>&1 | grep "MAC Address" | head -1 | awk -F" :" '{print $2}'`
    recordLog 2 "$IP_ADDR: lan print 8 (Sharelink) MAC : $lan8mac " "In Progress" "Upload File"
	 
    mac1=`echo $lan8mac|cut -d ":" -f1`  
    mac2=`echo $lan8mac|cut -d ":" -f2`
    mac3=`echo $lan8mac|cut -d ":" -f3`
    mac4=`echo $lan8mac|cut -d ":" -f4`
    mac5=`echo $lan8mac|cut -d ":" -f5`
    mac6=`echo $lan8mac|cut -d ":" -f6`
    check_mac_get $mac1 $mac2 $mac3 $mac4 $mac5 $mac6 ;

    lan_ded=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0x11 0x00 0x06 0x08 0x00 2>&1`
    recordLog 2 "$IP_ADDR: Real Dedicated MAC : $lan_ded " "In Progress" "Upload File"

    mac1=`echo $lan_ded|cut -d " " -f2`
    mac2=`echo $lan_ded|cut -d " " -f3`
    mac3=`echo $lan_ded|cut -d " " -f4`
    mac4=`echo $lan_ded|cut -d " " -f5`
    mac5=`echo $lan_ded|cut -d " " -f6`
    mac6=`echo $lan_ded|cut -d " " -f7`
    check_mac_get $mac1 $mac2 $mac3 $mac4 $mac5 $mac6 ;
    if [ $? -eq 1 ]
    then
        lan_ded="$mac1:$mac2:$mac3:$mac4:$mac5:$mac6"
    fi

}

#将sharelink mac 设置到dedicated mac上
function lan1mac_set()
{
	recordLog 2  "$IP_ADDR: Set lan 1 mac:" "In Progress" "Upload File"
#	lan1mac=`cat $LAN1_FILE`
#	lan8mac=`cat $LAN8_FILE`
#   lan_ded=`cat $DED_FILE`
    

	if [ "$lan8mac" == "00:00:00:00:00:00" ]
	then
		recordLog 2 "$IP_ADDR:Set Sharenic MAC Failed for MAC INVALID, please check after update!!" "In Progress" "Upload File"
		return 255
	fi
    if [ "$lan_ded" != "$lan8mac" ]
    then
        mac1=`echo $lan8mac|cut -d ":" -f1`  
	    mac2=`echo $lan8mac|cut -d ":" -f2`
	    mac3=`echo $lan8mac|cut -d ":" -f3`
	    mac4=`echo $lan8mac|cut -d ":" -f4`
	    mac5=`echo $lan8mac|cut -d ":" -f5`
	    mac6=`echo $lan8mac|cut -d ":" -f6`
	    check_mac_set $mac1 $mac2 $mac3 $mac4 $mac5 $mac6 ;
	    if [ $? -ne 0 ]
	    then
    		recordLog 2 "$IP_ADDR:Set mac lan 1 address failed, stop update!!" "In Progress" "Upload File"
    		return 255
	    fi
	    flashmac 0 $mac1 $mac2 $mac3 $mac4 $mac5 $mac6
	    if [ $? -ne 0 ]
	    then
    		recordLog 2 "$IP_ADDR:Set mac lan 1 address failed!" "In Progress" "Upload File"
    		return 255
	    fi
	    return 0
    else
        recordLog 2 "$IP_ADDR: lan 8 mac is same as lan dedicated mac " "In Progress" "Upload File"
        return 0
    fi
}



#get set hostname
lenSetHostnameConf=130
#mode - 1 for check and set host name, default
#mode - 0 for check host name only
mode=1
function formatFromStringToArray()
{
	if [ -e $HOSTNAME_FILE ]
	then
		rm $HOSTNAME_FILE
	fi

	SN="$1"
	lenHostname=${#SN}
	
	#invalid host name
	if [ $lenHostname -eq 0 ]
	then
		recordLog 2 "$IP_ADDR: SN invalid -- $SN!!!" "" ""
		return 255
	fi

	SNarry[0]=`echo 0x00`
	#((len=16#$lenHostname))
	#arry[1]=`echo $lenHostname`
	if [ $lenHostname -ge 15 ]
	then
		SNarry[1]=`printf "0x%x" $lenHostname `
	else
		SNarry[1]=`printf "0x0%x" $lenHostname `
	fi
	for((i=0;i<$lenHostname;i++))
	do
		achar=`echo ${SN:$i:(1)}`	
		SNarry[$i+2]=`printf "0x%02x" "'$achar" `
	done

	let i=2+$lenHostname
	while [ $i -lt $lenSetHostnameConf ]
	do
		SNarry[$i]=`echo 0x00`
		let i++
	done

	i=0
	while [ $i -lt $lenSetHostnameConf ]
	do
	 	echo -n "${SNarry[$i]} " >> $HOSTNAME_FILE
		let i++
	done
	echo "" >> $HOSTNAME_FILE
#	cat $HOSTNAME_FILE
}

function getHostnamecmd()
{
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x32 0x6b 0x01 0x00 2>&1`
#	res="01 03 33 32 31 00 00 00 00 00 00 00 00 00 00 00
# 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
# 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
# 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
# 00 00"
#	echo $res
	i=1
	while [ $i -lt 131 ]
	do	
		arry[$i]=`echo $res | awk -F ' ' '{print $'$i'}'`
		let i++
	done

	i=1
	while [ $i -lt 131 ]
	do
		if [ "${arry[$i]}" == "" ]
		then
			break;
		fi
		arry[$i]=`echo -n "0x${arry[$i]}"`
		let i++
	done
	return 0
}

function getProductSerial()
{
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD fru 2>&1 | grep " Product Serial" | head -1 | awk -F ' ' '{print $4}'`
	recordLog 2 "$IP_ADDR: Check Product Serial, SN:$res"  "In Progress" "Upload File"
	
}

function getSharelinkIPSource()
{
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 8 2>&1 | grep "IP Address Source" | head -1 | awk -F ' ' '{print $5}'`
	recordLog 2 "$IP_ADDR: Sharelink IP Address Source:$res"  "In Progress" "Upload File"
}

function getDedicatedIPSource()
{
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD lan print 1 2>&1 | grep "IP Address Source" | head -1 | awk -F ' ' '{print $5}'`
	recordLog 2 "$IP_ADDR: Dedicated IP Address Source:$res"  "In Progress" "Upload File"
}

function getSNFromFru()
{
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD fru 2>&1 | grep " Product Serial" | head -1 | awk -F ' ' '{print $4}'`
	recordLog 2 "$IP_ADDR: Check Host name, SN:$res" "Start"
	formatFromStringToArray $res
}

function compareSNToHostname()
{
	i=0
	while [ $i -lt $lenSetHostnameConf ]
	do
		if [ "${arry[$i+1]}" == "${SNarry[$i]}" ]
		then
			let i++
			continue
		else
		    recordLog 2 "$i: ${arry[$i+1]}!=${SNarry[$i]}" "Start"
		    recordLog 2 "hostname not same as SN, return......" "Start"
		    return 1
		fi
		
		let i++
	done
	
	return 0
}

function set_host_name()
{
#	ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x32 0x6c 0x01 0x00 $hostname_cmd

	recordLog 2 "$IP_ADDR: Start Set host Name" "Start"
	hostname_cmd=`cat $HOSTNAME_FILE`
	recordLog 2 "$IP_ADDR: set Hostname raw 0x32 0x6c 0x01 0x00 $hostname_cmd " "Start"
	ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x32 0x6c 0x01 0x00 $hostname_cmd 2>&1
	sleep 10 
	recordLog 2 "$IP_ADDR: Set hostname OK "  "Start"

	recordLog 2 "$IP_ADDR: Restart DNS" "Start"
	ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x32 0x6c 0x07 0x00 2>&1   
	sleep 60
	waitz $IP_ADDR

	recordLog 2 "$IP_ADDR: Restart BMC" "Start"
	ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc reset cold 2>&1
	sleep 120
	waitz $IP_ADDR

}

function checkAndSetHostname()
{
	if [ $# -eq 3 ] ; then
		recordLog 2 "$IP_ADDR: checkAndSetHostname $1 $2 $3" "Start"
		let mode=1
	elif [  $# -eq 4 ] ; then
		recordLog 2 "$IP_ADDR: checkAndSetHostname $1 $2 $3 $4" "Start"
		let mode=$4
		if [ $mode -eq 0 ]
		then
			recordLog 2 "$IP_ADDR: Check hostname only" "Start"
		fi
	else
	    echo "The num of parameter is wrong!" 
	    echo "Usage:checkAndSetHostname ip username password 
		  Note: Get SN and set to hostname, check the progress in logs/ip.txt"
	    return 255

	fi

	getSNFromFru
	getHostnamecmd
	compareSNToHostname
	sameflash=$?
	if [ $mode -eq 0 ]
	then
		return $sameflash
	fi

	if [ $sameflash -eq 0 ]
	then
		recordLog 2 "$IP_ADDR: ****Hostname is the same as SN!" "Start"
	else
		recordLog 2 "$IP_ADDR: Hostname NOT same as SN, set  Hostname as SN!" "Start"
		set_host_name
		getHostnamecmd
		compareSNToHostname
		if [ $? -eq 0 ]
		then
			recordLog 2 "$IP_ADDR: Hostname set DONE!! Hostname is the same as SN!" "Start"
			return 0
		else
			recordLog 2 "$IP_ADDR: ####Setted and Check Failed, Hostname not the same as SN!" "Start"
			return 255
		fi
	fi
}


function getProductSerial()
{ 
    PSN=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD fru print 0 2>&1 | grep "Product Serial" | head -1 | awk -F ' ' '{print $4}'`
    str="`date +"%Y%m%d%H%M%S"`_$PSN"
    LOG_DIR="$FILEPATH/update/$str"
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p $LOG_DIR
    fi
    LOG_FILE="$LOG_DIR/update.log"
    RESULT_SUCCESS="$FILEPATH/logs/resultSuccess.txt"
    RESULT_FAIL="$FILEPATH/logs/resultFail.txt"
    
}

function checkLogFile()
{
    #日志文件
    if [ ! -d "$LOG_DIR" ]; then  
    	mkdir -p $LOG_DIR
    else
        if [ -e $RESULT_SUCCESS ]
        then
            rm $RESULT_SUCCESS
        fi
        if [ -e $RESULT_FAIL ]
        then
            rm $RESULT_FAIL
        fi
    fi
    if [ ! -d "$TMP_DIR" ]; then  
    	mkdir -p $TMP_DIR
    fi

#    LOG_FILE="$LOG_DIR/$IP_ADDR.log"
#    TMP_FILE="$TMP_DIR/$IP_ADDR.tmp"
#    LAN1_FILE="$TMP_DIR/$IP_ADDR.lan1mac"
#    LAN8_FILE="$TMP_DIR/$IP_ADDR.lan8mac"
#    DED_FILE="$TMP_DIR/$IP_ADDR.landed"

}
function checkIpaddr()  
{
    echo $IP_ADDR | grep "^[0-9]\{1,3\}\.\([0-9]\{1,3\}\.\)\{2\}[0-9]\{1,3\}$" >/dev/null 2>&1
    if [ $? -ne 0 ];then 
        return 1
    fi

    a=`echo $IP_ADDR|awk -F . '{print $1}'`
    b=`echo $IP_ADDR|awk -F . '{print $2}'`  
    c=`echo $IP_ADDR|awk -F . '{print $3}'`  
    d=`echo $IP_ADDR|awk -F . '{print $4}'`  
    for num in $a $b $c $d  
    do  
        if [ $num -gt 255 ] || [ $num -lt 0 ];then 
            return 1
        fi  
    done

    return 0 
}

function checkBMCActive()
{
    for((i=0;i<2;i++))
    do
        ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc info 2>&1 |grep "Provides Device SDRs " >/dev/null 2>&1
        if [ $? = 0 ] ;then    
            recordLog 2  "$IP_ADDR BMC is Active, with user:$USER_NAME, pass:$USER_PASSWD" 
            return 0
        else
            recordLog 2  "$IP_ADDR BMC is not Active , with user:$USER_NAME, pass:$USER_PASSWD, time $i wait... " 
            sleep 2
        fi
    done

    #recordLog 2 "Failure: $IP_ADDR  BMC not response, please check BMC IP $IP_ADDR, user $USER_NAME, pass $USER_PASSWD"
    return 1
}

function preserveAll()
{
    sdr=1
    fru=1
    sel=1
    ipmi=1
    pef=1
    sol=1
    smtp=1
    user=1
    dcmi=1
    network=1
    ntp=1
    snmp=1
    ssh=1
    kvm=1
    authentication=1
    syslog=1
    hostname=1
}
function preserveAllExceptSdr()
{
    sdr=0
    fru=1
    sel=1
    ipmi=1
    pef=1
    sol=1
    smtp=1
    user=1
    dcmi=1
    network=1
    ntp=1
    snmp=1
    ssh=1
    kvm=1
    authentication=1
    syslog=1
    hostname=1
}
function preserveNone()
{
    sdr=0
    fru=0
    sel=0
    ipmi=0
    pef=0
    sol=0
    smtp=0
    user=0
    dcmi=0
    network=0
    ntp=0
    snmp=0
    ssh=0
    kvm=0
    authentication=0
    syslog=0
    hostname=0
}


function checkParameter()
{
    if [ "${2}x" != "x" ]
    then
        IP_ADDR=${2}
    fi
    if [ "${3}x" != "x" ]
    then
       USER_NAME=${3}
    fi
    if [ "${4}x" != "x" ]
    then
       USER_PASSWD=${4}
    fi
    if [ "${5}x" != "x" ]
    then
        BIN_FILE=${5}
    fi
    if [ "${6}x" != "x" ]
    then
        PRESERVE_OPTION=${6}
    fi
    if [ "${7}x" != "x" ]
    then
        IMAGE_UPDATA=${7}
    fi
    if [ "${8}x" != "x" ]
    then
        BOOT_IMAGE=${8}
    fi
    getProductSerial
    
    #check ip addr
    checkIpaddr $IP_ADDR
    if [ $? -ne 0 ]
    then
    	recordLog 4 "$IP_ADDR Failure: IP Address is not correct, please check!!" "Start" "Upload File"
    	return 255
    fi
    
    #check BMC bin File
    if [ ! -f "$BIN_FILE" ]
    then
    	recordLog 4  "$IP_ADDR Failure: Bin file '$BIN_FILE' Not exist, stop update" "Start" "Upload File"
    	return 255
    fi
    recordLog 2 "$IP_ADDR Select Bin file=$BIN_FILE" "Start"
    
    
    #参数个数判断
    if [[ $# -lt 5 ||  $# -gt 8 ]] ; then
        recordLog 4 "$IP_ADDR Failure: The num of parameter is wrong!" "Start" "Upload File"
        printHelp
        return 255
    fi
    if [ "$PRESERVE_OPTION" == "1" ]
    then
        preserveAll
        recordLog 2 "$IP_ADDR Preserve all option" "Start" "Upload File"
    elif  [ "$PRESERVE_OPTION" == "0" ]
    then
        preserveAllExceptSdr
        recordLog 2 "$IP_ADDR Preserve all option except sdr" "Start" "Upload File"
    elif  [ "$PRESERVE_OPTION" == "2" ]
    then
        PRESERVE_OPTION="0"
        preserveNone
        recordLog 2 "$IP_ADDR Preserve None option" "Start" "Upload File"
    else
        recordLog 2 "$IP_ADDR Error: the parameter PRESERVE_OPTION should be 0 or 1,2" "Start" "Upload File"
        printHelp
        return 255
    fi
        
    if [ "$sdr" != "0" -a "$sdr" != "1" ] || [ "$fru" != "0" -a "$fru" != "1" ] || [ "$sel" != "0" -a "$sel" != "1" ] || [ "$ipmi" != "0" -a "$ipmi" != "1" ] || [ "$pef" != "0" -a "$pef" != "1" ] || [ "$sol" != "0" -a "$sol" != "1" ] ||
       [ "$smtp" != "0" -a "$smtp" != "1" ] || [ "$user" != "0" -a "$user" != "1" ] || [ "$dcmi" != "0" -a "$dcmi" != "1" ] || [ "$network" != "0" -a "$network" != "1" ] || [ "$ntp" != "0" -a "$ntp" != "1" ] || [ "$snmp" != "0" -a "$snmp" != "1" ] ||
       [ "$ssh" != "0" -a "$ssh" != "1" ] || [ "$kvm" != "0" -a "$kvm" != "1" ] || [ "$authentication" != "0" -a "$authentication" != "1" ] || [ "$syslog" != "0" -a "$syslog" != "1" ] || [ "$hostname" != "0" -a "$hostname" != "1" ]
    then
        recordLog 4 "$IP_ADDR Failure: preserve configuration is not 0 or 1 ,please check preserve configuration file" "Start" "Upload File"
        printHelp
        return 255
    fi

    if [ "$IMAGE_UPDATA" == "0" ] || [ "$IMAGE_UPDATA" == "1" ] || [ "$IMAGE_UPDATA" == "2" ] || [ "$IMAGE_UPDATA" == "3" ]
    then
        recordLog 2 "$IP_ADDR IMAGE_UPDATA:$IMAGE_UPDATA" "Start"
    else
        recordLog 4 "$IP_ADDR Failure: the parameter IMAGE_UPDATA should be one of 0,1,2,3" "Start" "Upload File"
        printHelp
        return 255
    fi

    if [ "$BOOT_IMAGE" == "0" ] || [ "$BOOT_IMAGE" == "1" ] || [ "$BOOT_IMAGE" == "2" ] || [ "$BOOT_IMAGE" == "3" ] || [ "$BOOT_IMAGE" == "4" ] || [ "$BOOT_IMAGE" == "5" ]
    then
        recordLog 2 "$IP_ADDR BOOT_IMAGE:$BOOT_IMAGE" "Start" "Upload File"
    else
        recordLog 4 "$IP_ADDR Failure: The parameter BOOT_IMAGE should be one of 0,1,2,3,4,5" "Start" "Upload File"
        printHelp
        return 255
    fi
    HOSTNAME_FILE="$FILEPATH/logs/$IP_ADDR.hostname"
    return 0
}


function bmcUpdate()
{
    checkLogFile
    #printToolVersion

    checkParameter $@
    if [ $? -ne 0 ]
    then
        recordLog 4  "$IP_ADDR Parameter error,please check." "Start"
        exit 255
    fi

    checkBMCActive
    if [ $? -ne 0 ]
    then
        recordLog 4  "$IP_ADDR BMC not Update, BMC not response, please check ip $IP_ADDR, user $USER_NAME, pass $USER_PASSWD" "Start"
        exit 255
    fi
    
    check_productName_fru
    if [ $? -ne 0 ]
	then
		exit 255
	fi
	
    if [ "$SUPPORT" == "0" ]
    then
    	recordLog 4  "$IP_ADDR: Product Name $PN is not supported" "Start"
    	exit 255
    fi
        
    lanmac_get
    #判断是不是sharelink网络
    checklan8ip $IP_ADDR 
    if [ $? -ne 1 ]
    then
    	recordLog 2  "$IP_ADDR  is using sharelink ip." "Start"
    	getSharelinkIPSource
    	#判断机型
        if [ "$PN" == "SA5212M5" -o "$PN" == "NF5280M5" -o "$PN" == "NF5180M5" -o "$PN" == "SA5112M5" ]
        then
            lan1mac_set
            if [ $? -ne 0 ]
            then
                recordLog 2  "$IP_ADDR Set mac lan 1 address failed." "Start"
                exit 255
            fi
        fi
    else
        getDedicatedIPSource
    fi
    getProductSerial
    getfwversion

    #before update bmc reset
    #res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc reset cold 2>&1`
    #recordLog 2 "$IP_ADDR: Reset bmc, wait to update..." "Start"
    #sleep 150
    #waitz $IP_ADDR

    recordLog 2 "$IP_ADDR: Update start"  "In Progress" "Upload File"

    #upgrade bmc
    flash_node $IP_ADDR
    if [ $? -ne 0 ]
    then
    	#recordLog 4 "$IP_ADDR: Update failed ,Some thing not OK, please check!!"
    	exit 1
    fi

    #record end version
    getfwversion
    #record end lan
    #lanmac_get
    
    #if [ "$PN" == "SA5212M5" -o "$PN" == "NF5280M5" -o "$PN" == "NF5180M5" -o "$PN" == "SA5112M5" ]
    #then
    #   recordLog 2 "Check and set HostName now..." "Start"
    #    checkAndSetHostname $IP_ADDR $USER_NAME $USER_PASSWD
    #    if [ $? -ne 0 ]
     #   then
     #   	recordLog 2 "$IP_ADDR: Hostname NOT the same as SN" "Start"
     #   fi
    #fi
}

function batbmcUpdate()
{

    checkParameter $@
    if [ $? -ne 0 ]
    then
        recordLog 4  "$IP_ADDR  Parameter error,please check." "Start"
        return 255
    fi
    
    checkBMCActive
    if [ $? -ne 0 ]
    then
        recordLog 4  "$IP_ADDR BMC not Update, BMC not response, please check ip $IP_ADDR, user $USER_NAME, pass $USER_PASSWD"
        return 255
    fi
    
    check_productName_fru
    if [ $? -ne 0 ]
	then
		return 255
	fi
    if [ "$SUPPORT" == "0" ]
    then
    	recordLog 4  "$IP_ADDR: Product Name $PN is not supported"
    	return 255
    fi
    
    lanmac_get
    if [ $? -ne 0 ]
	then
		return 255
	fi

    #判断是不是sharelink网络
    checklan8ip $IP_ADDR 
    if [ $? -ne 1 ]
    then
    	recordLog 2  "$IP_ADDR  is using sharelink ip."
    	getSharelinkIPSource
    	if [ "$PN" == "SA5212M5" -o "$PN" == "NF5280M5" -o "$PN" == "NF5180M5" -o "$PN" == "SA5112M5" ]
        then
            lan1mac_set
            if [ $? -ne 0 ]
            then
                recordLog 2  "$IP_ADDR: Set mac lan 1 address failed."
                return 255
            fi
        fi
    else
        getDedicatedIPSource
    fi

    getfwversion
    
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc reset cold 2>&1`
    recordLog 2 "$IP_ADDR: Reset bmc, wait to update..."
    sleep 150	
    waitz $IP_ADDR

    recordLog 2 "$IP_ADDR: Update start"

    #upgrade bmc
    flash_node $IP_ADDR
    if [ $? -ne 0 ]
    then
    	#recordLog 4 "$IP_ADDR: Update failed ,Some thing not OK, please check!!"
    	return 201
    fi

    #record end version
    getfwversion
    #record end lan
    lanmac_get
    
    if [ "$PN" == "SA5212M5" -o "$PN" == "NF5280M5" -o "$PN" == "NF5180M5" -o "$PN" == "SA5112M5" ]
    then
        recordLog 2 "Check and set HostName now..."
        checkAndSetHostname $IP_ADDR $USER_NAME $USER_PASSWD
        if [ $? -ne 0 ]
        then
        	recordLog 2 "$IP_ADDR: Hostname NOT the same as SN"
        fi
    fi
    return 0
}


function batchBMCUpdate()
{
    #check Log File
    checkLogFile
    #printToolVersion
    
    #clear stop file
    if [ -e $STOP_FILE ]
    then
    	rm -f $STOP_FILE
    fi
    
    if [ ! -f "$IP_FILE" ]
    then
        echo  "bmc configuration file $IP_FILE Not exist, please check"
        exit 1
    fi
    
    if [ "x$THREAD_NUM" == "x" ]
    then
        THREAD_NUM=20
    else
        if echo $THREAD_NUM | grep  -q '[^0-9]'
        then
            THREAD_NUM=20
        fi
    fi
    
    #judge max Thread Num
    currentThreadNum=$THREAD_NUM
    if [ ${currentThreadNum} -gt ${THREAD_MAX} ]
    then
        currentThreadNum=$THREAD_MAX
        echo "Thread num will set to $THREAD_MAX, when setting is greater than max thread"
    fi
    recordLog 2 "Current Thread Num is $currentThreadNum"

    tmpFIFO="/tmp/fdscan2"
    #echo "Tmp FIFO file is:$tmpFIFO"
    mkfifo $tmpFIFO
    exec 3<>$tmpFIFO
    rm -f $tmpFIFO

    for ((i=0;i<${currentThreadNum};i++))
    do
        echo >&3
    done 

    for LINE in `cat $IP_FILE`
    do
    {
        #stop batch
        if [ -f $STOP_FILE ]
        then
            echo "----------------------"
            echo "detect batch stop command, Tool will not start new thread,please wait threads to stop"
            echo "-------------------------------------------------------"
            rm -f $STOP_FILE
            break
        fi
        # ignore start with # line
        if [[ $LINE =~ ^#.* ]]
        then
            echo "this line is pass:$LINE"
            continue
        else
            echo "this line is:$LINE"
        fi
        
        
    	IP_ADDR=`echo $LINE |awk -F ',' '{print $1}'`
    	checkIpaddr $IP_ADDR
    	if [ $? -ne 0 ]
        then
        	recordLog 4 "$IP_ADDR: IP Address is not correct, please check!!"
        	continue
        fi
    	USER_NAME=`echo $LINE |awk -F ',' '{print $2}'`
    	USER_PASSWD=`echo $LINE |awk -F ',' '{print $3}'`
    	

    	if [ "$BIN_FILEA" == "" ]
    	then
    	    BIN_FILE=`echo $LINE  |awk -F ',' '{print $4}'`
    	else
    	    BIN_FILE=$BIN_FILEA
    	fi
    	
    	
    	if [ ! -f "$BIN_FILE" ]
        then
        	recordLog 4  "$IP_ADDR  BMC image upgrade file $BIN_FILE does not exist"
        	continue
        fi
    	
        
    	PRESERVE_OPTION=`echo $LINE  |awk -F ',' '{print $5}'`
    	if [ "$PRESERVE_OPTION" == "" ]
        then
            PRESERVE_OPTION=1
        elif  [ "$PRESERVE_OPTION" == "0" -o "$PRESERVE_OPTION" == "1" -o "$PRESERVE_OPTION" == "2" ]
        then
            PRESERVE_OPTION=$PRESERVE_OPTION 
        else
            recordLog 4  "$IP_ADDR The input PRESERVE_OPTION:$PRESERVE_OPTION Error, the PRESERVE_OPTION should be 0 ,1 or 2"
            continue
        fi
        
        OPTION_UPDATE=`echo $LINE  |awk -F ',' '{print $6}'`
    	if [ "$OPTION_UPDATE" == "" ]
        then
            IMAGE_UPDATA=3
        elif  [ "$OPTION_UPDATE" == "0" -o "$OPTION_UPDATE" == "1" -o "$OPTION_UPDATE" == "2" -o "$OPTION_UPDATE" == "3" ]
        then
            IMAGE_UPDATA=$OPTION_UPDATE 
        else
            IMAGE_UPDATA=3
            recordLog 2  "The input IMAGE_UPDATA OPTION Error, the Image_update will set to default both"
        fi
        
        OPTION_BOOT=`echo $LINE  |awk -F ',' '{print $7}'`
    	if [ "$OPTION_BOOT" == "" ]
        then
            BOOT_IMAGE=0
        elif  [ "$OPTION_BOOT" == "0" -o "$OPTION_BOOT" == "1" -o "$OPTION_BOOT" == "2" -o "$OPTION_BOOT" == "3" -o "$OPTION_BOOT" == "4" -o "$OPTION_BOOT" == "5" ]
        then
            BOOT_IMAGE=$OPTION_BOOT    
        else
            BOOT_IMAGE=0
            recordLog 2  "The input BOOT_IMAGE OPTION Error, the boot_image will set to default highVersion"
        fi
    	
    	#echo "IP_ADDR:$IP_ADDR      USER_NAME:$USER_NAME    USER_PASSWD:$USER_PASSWD   BIN_FILE:$BIN_FILE  IMAGE_UPDATA:$IMAGE_UPDATA  BOOT_IMAGE:$BOOT_IMAGE"
    	
    	
    	recordLog 2 "bmcUpdate $IP_ADDR $USER_NAME $USER_PASSWD  $BIN_FILE $PRESERVE_OPTION $IMAGE_UPDATA  $BOOT_IMAGE"
    	if [ x"$IP_ADDR" != "x" ]
        then
            read -u3
            {
            	batbmcUpdate -s $IP_ADDR $USER_NAME $USER_PASSWD  $BIN_FILE $PRESERVE_OPTION $IMAGE_UPDATA  $BOOT_IMAGE
            	if [ $? -ne 0 ]
                then
                	recordLog 4 "$IP_ADDR: BMC update failed"
                else
                    recordLog 3  "$IP_ADDR: BMC update success" "Success"
                fi
                echo >&3
            } &
        fi

    }
    done
    wait
    recordLog 2 "All BMC update done" "Success"
    exec 3<&-
    exec 3>&-
    exit
}

#*****************************************************************
#convert hex data to dec
#*****************************************************************
function converthex2dec()
{
    hex=$1
    blerror=false

    if [[ $hex != "0" ]] && [[ $hex != "1" ]] && [[ $hex != "2" ]] && [[ $hex != "3" ]] && [[ $hex != "4" ]] && [[ $hex != "5" ]] && [[ $hex != "6" ]] && [[ $hex != "7" ]] && [[ $hex != "8" ]] && [[ $hex != "9" ]] && [[ $hex != "A" ]] && [[ $hex != "B" ]] && [[ $hex != "C" ]] && [[ $hex != "D" ]] && [[ $hex != "E" ]] && [[ $hex != "F" ]] && [[ $hex != "a" ]] && [[ $hex != "b" ]] && [[ $hex != "c" ]] && [[ $hex != "d" ]] && [[ $hex != "e" ]] && [[ $hex != "f" ]];then
        blerror=true
    fi  

    if [[ "$blerror" == "true" ]];then
        echo "false"
    elif [[ $hex == "A" ]] || [[ $hex == "a" ]];then
        echo "10"
    elif [[ $hex == "B" ]] || [[ $hex == "b" ]];then
        echo "11"
    elif [[ $hex == "C" ]] || [[ $hex == "c" ]];then
        echo "12"
    elif [[ $hex == "D" ]] || [[ $hex == "d" ]];then
        echo "13"
    elif [[ $hex == "E" ]] || [[ $hex == "e" ]];then
        echo "14"
    elif [[ $hex == "F" ]] || [[ $hex == "f" ]];then
        echo "15"
    else
        echo $hex
    fi  
}

#*****************************************************************
#TFlex Host Update Box BMC
#*****************************************************************
function TflexUpdateBoxBmc()
{
    checkLogFile
    printToolVersion

    checkParameter $@
    if [ $? -ne 0 ]
    then
        recordLog 2  "$IP_ADDR  Parameter error,please check."
        exit 255
    fi
    
    getfwversion
#####################
    ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD power status 2>&1
    if [ $? -ne 0 ];then
        recordLog 3 "$IP_ADDR BMC can not login,please check the IP,username or password etc."
    	exit 255
    fi
#####################
    
    check_productName_fru
    if [ "$SUPPORT" == "0" ]
    then
    	recordLog 2  "$IP_ADDR: #Product Name $PN is not supported"
    	exit 255
    fi
    

#xxxfor ((i=0; i<3; i++))
#xxxdo
#xxx    recordLog 2 "####Di $i Ci, total:$retrytimes#########"
#################################
    #Step: Get Login Info
    recordLog 2 "$IP_ADDR Start Login"
    for ((j=0; j<$retrytimes; j++))
    do
      toasciihex $USER_NAME
	  USERNAME=$asciiHex
	  toasciihex $USER_PASSWD
	  PASSWORD=$asciiHex
	  #admin=1e-1b-12-16-11
      webres=`curl -s --insecure --cookie-jar $TMP_DIR/cookies_$IP_ADDR --data "username=$USERNAME&password=$PASSWORD&encrypt_flag=1" https://$IP_ADDR/api/session`
      if [ $? -eq 0 ];then
        recordLog 2 "Login ok..."
        break
      else
        sleep 5
        recordLog 2 "Login error, retry..."
      fi
    done
      
    if [ $j -eq $retrytimes ];then
      recordLog 3 "$IP_ADDR BMC can not login,please check the IP,username or password etc."
      exit 5
    fi

      #Step4: Get cookie
      CSRFToken=`echo "$webres"|awk -F "CSRFToken" '{print $2}' |awk -F '"' '{print $3}'`
      
    res=`curl -s --insecure -X GET -H "X-CSRFTOKEN:$CSRFToken" -b $TMP_DIR/cookies_$IP_ADDR https://$IP_ADDR/api/maintenance/TflexSummary`
    #xxxxxxxxxxx res="[ { "TflexID": 0, "power_status": 1, "uid_status": 0, "fans_status": 0, "fans_redundancy": 0, "power_supplies_status": 2, "power_supplies_redundancy": 2, "voltage_status": 0, "temperature_status": 0 } { "TflexID": 1, "power_status": 1, "uid_status": 0, "fans_status": 0, "fans_redundancy": 0, "power_supplies_status": 2, "power_supplies_redundancy": 2, "voltage_status": 0, "temperature_status": 0 }]"
    recordLog 2 "get TflexSummary:$res"
    TflexID=`echo "$res"|grep -Po 'TflexID[":]+\K[^,]+'`
    for boxId in $TflexID;do
        recordLog 2 "box Id:$boxId"
        if [ "$boxId" == "0" ]
        then
            for ((n=0; n<3; n++))
            do
                res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0xe1 0x01 0x09 2>&1`
                if [ $? -ne 0 ]
            	then
            	    recordLog 2 "can not get box firmware version,retry...."
            		sleep 60
            		continue
            	fi
                res1=`echo $res | head -1 | awk -F ' ' '{print $1}'`
                res5=`echo $res | head -1 | awk -F ' ' '{print $5}'`
                res7=`echo $res | head -1 | awk -F ' ' '{print $7}'`
                res9=`echo $res | head -1 | awk -F ' ' '{print $9}'`
                recordLog 2 "box firmware version $res5.$res7.$res9"
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "00" ]] && [[ "$res7" == "00" ]] && [[ "$res9" == "00" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "FF" ]] && [[ "$res7" == "FF" ]] && [[ "$res9" == "FF" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        break
            done
            if [ $n -eq 3 ];then
                recordLog 3 "$IP_ADDR BMC can not get box firmware."
                exit 5
            fi

        fi
        if [ "$boxId" == "1" ]
        then
            sleep 480
            for ((m=0; m<3; m++))
            do
                res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0xe1 0x01 0x19 2>&1`
                if [ $? -ne 0 ]
            	then
            	    recordLog 2 "can not get box firmware version,retry...."
            		sleep 60
            		continue
            	fi
                res1=`echo $res | head -1 | awk -F ' ' '{print $1}'`
                res5=`echo $res | head -1 | awk -F ' ' '{print $5}'`
                res7=`echo $res | head -1 | awk -F ' ' '{print $7}'`
                res9=`echo $res | head -1 | awk -F ' ' '{print $9}'`
                recordLog 2 "box firmware version $res5.$res7.$res9"
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "00" ]] && [[ "$res7" == "00" ]] && [[ "$res9" == "00" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "FF" ]] && [[ "$res7" == "FF" ]] && [[ "$res9" == "FF" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        break
            done
            if [ $m -eq 3 ];then
                recordLog 3 "$IP_ADDR BMC can not get box firmware."
                exit 5
            fi
        fi
    
      
    ##################################
          #Step8: upload the image file
          recordLog 2 "Upload Image File"
    ###################################
        for ((j=0; j<$retrytimes; j++))
        do
          res=`curl -s --insecure  -H "X-CSRFTOKEN:$CSRFToken" -b $TMP_DIR/cookies_$IP_ADDR -F "fwimage=@$BIN_FILE;filename=$BIN_FILE;" https://$IP_ADDR/api/maintenance/tflexfirmware`
          if [ $? -eq 0 ];then
            result=`echo $res|grep "error"`
    	    if [ "$result" != "" ]
            then
        	    recordLog 2  "$IP_ADDR BoxId:$boxId failed to upload ,detail: $res"
        	    webres=`curl -s --insecure --cookie-jar $TMP_DIR/cookies_$IP_ADDR --data "username=$USERNAME&password=$PASSWORD&encrypt_flag=1" https://$IP_ADDR/api/session`
                if [ $? -eq 0 ];then
                    recordLog 2 "Login ok..."
                    CSRFToken=`echo "$webres"|awk -F "CSRFToken" '{print $2}' |awk -F '"' '{print $3}'`
                    continue
                else
                    sleep 5
                    recordLog 2 "Login error, retry..."
                fi
        	    continue
        	else
        	    recordLog 2 "Upload BMC image OK..."
                break
            fi
            
          else
            sleep 5
            recordLog 2 "Upload BMC image error, retry..."
            webres=`curl -s --insecure --cookie-jar $TMP_DIR/cookies_$IP_ADDR --data "username=$USERNAME&password=$PASSWORD&encrypt_flag=1" https://$IP_ADDR/api/session`
            if [ $? -eq 0 ];then
                recordLog 2 "Login ok..."
                CSRFToken=`echo "$webres"|awk -F "CSRFToken" '{print $2}' |awk -F '"' '{print $3}'`
                continue
            else
                sleep 5
                recordLog 2 "Login error, retry..."
            fi
          fi
        done
        
        
        recordLog 2 "upload BMC image result:$res"
          
        if [ $j -eq $retrytimes ];then
          recordLog 3 "Upload BMC image error"
          exit 8
        fi
    ####################################
          #Step9: Image verify

          #Step10:Start update the Image
          #recordLog 2 "Start Updating tflexfirmware preserve"
          #preserve=`curl -s --insecure -H "X-CSRFTOKEN:$CSRFToken" -b $TMP_DIR/cookies_$IP_ADDR -X PUT -H "Content-Type:application/json" -d '{"preserve_config":1,"flash_status":1}' https://$IP_ADDR/api/maintenance/tflexfirmware`
          #recordLog 2 "end to preserve:$preserve"
          
          recordLog 2 "Start TflexBMCFlash"
          res=`curl -s --insecure -H "X-CSRFTOKEN:$CSRFToken" -b $TMP_DIR/cookies_$IP_ADDR -X PUT -H "Content-Type:application/json" -d '{"TflexID":"'$boxId'"}' https://$IP_ADDR/api/maintenance/firmware/TflexBMCFlash`
          recordLog 2 "end TflexBMCFlash:$res"
          
          recordLog 2 "get TflexBMCFlash progress"
          res=`curl -s --insecure -H "X-CSRFTOKEN:$CSRFToken" -b $TMP_DIR/cookies_$IP_ADDR -X GET -H "Content-Type:application/json" https://$IP_ADDR/api/maintenance/tflexfirmware/transfer-progress`
          recordLog 2 "end TflexBMCFlash progress :$res"
          sleep 30
          
        #sleep 30 mintus
        for ((j=0; j<30; j++))
        do
          sleep 60
          recordLog 2 "get TflexBMCFlash progress"
          res=`curl -s --insecure -H "X-CSRFTOKEN:$CSRFToken" -b $TMP_DIR/cookies_$IP_ADDR -X GET -H "Content-Type:application/json" https://$IP_ADDR/api/maintenance/tflexfirmware/transfer-progress`
          result=`echo $res|grep "error"`
    	  if [ "$result" != "" ]
          then
        	recordLog 2  "$IP_ADDR BoxId:$boxId failed to get progress ,detail: $res"
        	break
          fi
          recordLog 2 "end TflexBMCFlash progress :$res"
          progress=`echo $res | awk -F 'progress' '{print $2}' | awk -F '\"' '{print $3}'`
    	  if [ $? -ne 0 ]
    	  then
    	        progress=0
    	        break
    	  fi

    	  if [ "$progress" == "Complete..." ] || [ "$progress" == "Completed." ] || [ "$progress" == "completed." ] || [ "$progress" == "Success..." ]
    	  then
    		let progress=100
    		recordLog 3 "$IP_ADDR: Box bmc update:${progress} %"
    		#recordLog 2 "$IP_ADDR: Update success,box bmc will auto restart!"
    		break
    	  else
    	    progress=`echo $progress | awk -F '%' '{print $1}'`
    	  fi
    	  progressState=`echo $res | awk -F 'state' '{print $2}' |awk -F ":" '{print $2}' |awk -F "}" '{print $1}'`
    	  if [ "$progressState" == " 2 " ]
          then
        	let progress=100
        	break
          fi
        done

        delete_session
        if [ "$progress" == "100" ]
        then
        	recordLog 2 "BMC Update success"
        fi
        sleep 300
        if [ "$boxId" == "0" ]
        then
            for ((m=0; m<10; m++))
            do
                res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0xe1 0x01 0x09 2>&1`
                if [ $? -ne 0 ]
            	then
            	    recordLog 2 "can not get box firmware version,retry...."
            		sleep 60
            		continue
            	fi
                res1=`echo $res | head -1 | awk -F ' ' '{print $1}'`
                res5=`echo $res | head -1 | awk -F ' ' '{print $5}'`
                res7=`echo $TMPres_FILE | head -1 | awk -F ' ' '{print $7}'`
                res9=`echo $res | head -1 | awk -F ' ' '{print $9}'`
                recordLog 2 "box firmware version $res5.$res7.$res9"
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "00" ]] && [[ "$res7" == "00" ]] && [[ "$res9" == "00" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "FF" ]] && [[ "$res7" == "FF" ]] && [[ "$res9" == "FF" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        break
            done
            if [ $m -eq 10 ];then
                recordLog 3 "$IP_ADDR BMC can not get box firmware."
                exit 5
            fi

        fi
        if [ "$boxId" == "1" ]
        then
            for ((n=0; n<10; n++))
            do
                res = `ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0xe1 0x01 0x19 2>&1`
                if [ $? -ne 0 ]
            	then
            	    recordLog 2 "can not get box firmware version,retry...."
            		sleep 60
            		continue
            	fi
                res1=`cat $res | head -1 | awk -F ' ' '{print $1}'`
                res5=`cat $res | head -1 | awk -F ' ' '{print $5}'`
                res7=`cat $res | head -1 | awk -F ' ' '{print $7}'`
                res9=`cat $res | head -1 | awk -F ' ' '{print $9}'`
                recordLog 2 "box firmware version $res5.$res7.$res9"
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "00" ]] && [[ "$res7" == "00" ]] && [[ "$res9" == "00" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        if [[ $res1 == "01" ]] && [[ "$res5" == "FF" ]] && [[ "$res7" == "FF" ]] && [[ "$res9" == "FF" ]]
    	        then
    	            recordLog 2 "can not get box firmware version,retry..."
    	            sleep 60
    	            continue
    	        fi
    	        break
            done
            if [ $n -eq 10 ];then
                recordLog 3 "$IP_ADDR BMC can not get box firmware."
                exit 5
            fi
        fi
        getfwversion
        recordLog 2 "BMC Update Over"
    done
#xxxdone
      
exit 0
}


case $1 in

        -h|--help|-H)
		    printHelp
    		exit
            ;;
        -b|-B|--batch)
            IP_FILE=$2
            THREAD_NUM=$3
            batchBMCUpdate $@
            exit
            ;;
        -s|-S|--single)
            bmcUpdate $@
            exit
            ;;
        -stop)
			echo "Stop Batch Update execute"
			stopBatch
			exit
			;;
        -box)
            TflexUpdateBoxBmc $@
            exit
            ;;
        *)
            printHelp
            exit
            ;;       
esac


