#!/bin/bash

#file path
FILEPATH=$(cd `dirname $0`;pwd)

########################################
VERSION=V1R1
MODIFY_DATE=20190315
########################################

########################################
IP_ADDR=""
USER_NAME="root"
USER_PASSWD="root"
BIN_FILE=""
#PRESERVE: 1-PRESERVE BIOS Setup Options; 0-Not PRESERVE BIOS Setup Options.
SYNCMODE=99
USERNAME=""
PASSWORD=""
########################################

########################################
LOG_DIR="$FILEPATH/update/"
LOG_FILE="$LOG_DIR/update.log"
RESULT_SUCCESS="$FILEPATH/logs/resultSuccess.txt"
RESULT_FAIL="$FILEPATH/logs/resultFail.txt"
#support
SUPPORT="0"
asciiHex=""
CSRFToken=""
cookies=""
#product name
PN=""
PSN=""
#fail retrytime
retrytimes=3
#########################################

#######Thread set#############################
THREAD_MAX=200
THREAD_NUM=20
STOP_FILE="$FILEPATH/batchstop"
###########################################

############in band###################
AFULNX="afulnx_64"
IPMITOOL="ipmitool"
######################################


function printHelp()
{
    echo "Usage:    ./firmware_update.sh [cmd] [param]"
    echo "    cmd: "
    echo "        -s    Single firmware  Update"
    echo "    param:"
    echo "        Reference different cmd"
    echo
    echo 
    echo "firmware update Usage: ./firmware_update.sh -s <ip>  <username>  <password>  <iamgeFile>  [syncmode]"
    echo "       ip                     BMC ip Address"
    echo "       username               BMC user name"
    echo "       password               BMC user password"
    echo "       iamgeFile              frimware upgrade image file"
    echo "       syncmode               optional(default:0)  firmware preserve setup options:1-syncmode, 0-not syncmode."
    echo 
    echo "example  ./firmware_update.sh 100.2.2.2 root root hpm"
    echo "         ./firmware_update.sh 100.2.2.2 root root hpm 1"
}



#print tool version
function printToolVersion()
{
    recordLog 2 "firmware upgrade Tool Version:$VERSION   date:$MODIFY_DATE" "Start" "Upload File"
}

function checkBMCActive()
{
    for((i=0;i<2;i++))
    do
        ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD mc info 2>&1 |grep "Provides Device SDRs " >/dev/null 2>&1
        if [ $? = 0 ] ;then    
            recordLog 2  "$IP_ADDR BMC is Active, with user:$USER_NAME, pass:$USER_PASSWD" "Upload File"
            return 0
        else
            recordLog 2  "$IP_ADDR BMC is not Active , with user:$USER_NAME, pass:$USER_PASSWD, time $i wait... "  ""
            sleep 2
        fi
    done

    #recordLog 2 "Failure: $IP_ADDR  BMC not response, please check BMC IP $IP_ADDR, user $USER_NAME, pass $USER_PASSWD" ""
    return 1
}


#record log
function recordLog()
{
    note=`echo $2|sed -r 's/"//g'`
    if [ $1 -eq 1 ]
    then
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
    elif [ $1 -eq 2 ]
    then
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
    elif [ $1 -eq 3 ]
    then
        #only success log file
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
    elif [ $1 -eq 4 ]
    then
        # failure log
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} "
        echo "{\"time\": `date`,\"Stage\": \"$4\",\"State\":\"$3\" \"Note\":\"$note\"} " >> $LOG_FILE
    elif [ $1 -eq 5 ]
    then
        # failure log
        echo -ne "{\"time\": `date`,\"Stage\": \"In Progress\",\"State\":\"Success\" \"Note\":\"\e$note\"} "
        echo -ne "{\"time\": `date`,\"Stage\": \"In Progress\",\"State\":\"Success\" \"Note\":\"\e$note\"} " >> $LOG_FILE
    else
        return ;    
    fi    
}

dec2hex(){
    printf "%x" $1
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

function checkEnv()
{
    curl -V >/dev/null 2>&1
    if [ $? = 0 ] ;then
        #echo "[ok] curl is installed..."
        :
    else
        echo "[Error]: curl is not detected,please install first."
        exit 101
    fi

    ipmitool -V >/dev/null 2>&1
    if [ $? = 0 ] ;then
        #echo "[ok] ipmitool is installed..."
        :
    else
        echo "[Error] ipmitool is not detected,please install first."
        exit 101
    fi
}

function getfwversion()
{
    #get BMC Version
    res=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0x37 0x00  2>&1`
    if [ $? -ne 0 ]
	then
		#recordLog 2 "${IP_ADDR}: Get BMC Version Failed!"
		return 255
	fi
	verison1=`echo ${res} | awk -F ' ' '{print $3}'`
	verison2=`echo ${res} | awk -F ' ' '{print $4}'`
	verison3=`echo ${res} | awk -F ' ' '{print $5}'`
	bmcVersion=`printf "%d.%d.%d" 0x0${verison1} 0x0${verison2} 0x0${verison3}`
	recordLog 2 "${IP_ADDR} Current BMC Version: ${bmcVersion}" "Start" "Upload File"
	
    #get BIOS Version
    #resBios=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD raw 0x3c 0x03 0x01 0x00  2>&1`
    #if [ $? -ne 0 ]
	#then
	#	#recordLog 2 "$IP_ADDR Get BIOS Version Failed!!"
	#	return 255
	#fi
	#
	#let i=1
	#while [ $i -lt 31 ]
	#do	
	#	arry[$i]=`echo $resBios | awk -F ' ' '{print $'$i'}'`
	#	((tmp=0x${arry[$i]}))
	#	biosVersion=$biosVersion`echo $tmp | awk '{printf("%c", $tmp)}'`
	#	let i++
	#done
    #recordLog 2 "${IP_ADDR} This BIOS version is $biosVersion" "Start" "Upload File"
    return 0
}

PNLIST=(SA5212T6,Product)
function check_productName_fru()
{ 
    PN=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD fru print 0 2>&1 | grep " Product Name" | head -1 | awk -F ' ' '{print $4}'`
    if echo "${PNLIST[@]}" | grep -w "$PN" &>/dev/null; then
        recordLog 2 "$IP_ADDR Product Name is $PN" "Start" "Upload File"
        SUPPORT="1"
        return 0
    else
        recordLog 2 "$IP_ADDR Product Name is $PN" "Start" "Upload File"
        SUPPORT="0"
        return 255
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

#
function create_session()
{
    #get session
    FAIL_COUNT=0
    for ((i=1; i<=$retrytimes; i++))
    do
        webres=`curl -s --cookie-jar cookies_$IP_ADDR -X POST  --data "username=$USERNAME&password=$PASSWORD&encrypt_flag=1" https://$IP_ADDR/api/session --insecure`
        result=`echo $webres|grep "error"`
        if [ "$result" != "" ]
        then
            let FAIL_COUNT++
            sleep 10
        else
            CSRFToken=`echo "$webres"|awk -F "CSRFToken" '{print $2}' |awk -F '"' '{print $3}'`
            cookies=`cat cookies_$IP_ADDR|grep  QSESSIONID |awk -F "QSESSIONID" '{print $2}'| sed 's/^[ \t]*//g'`
            #echo "CSRFToken:$CSRFToken"
            #echo "cookies:$cookies"
            break
        fi
    done
    if [ $FAIL_COUNT -eq $retrytimes ];then
        recordLog 4  "$IP_ADDR Failed to get session,detail: $webres" "Upload File"
        return 255
    fi
    recordLog 2  "$IP_ADDR Success to create session" "Start" "Upload File"
}

function deleteSession()
{
    res=`curl -s -X DELETE --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken"  https://$IP_ADDR/api/session --insecure`
    result=`echo $res|grep "error"`
    if [ "$result" != "" ]
    then
        recordLog 2  "$IP_ADDR Failed to close session: $res" "" "Activate"
        return 255
    fi
    recordLog 2 "$IP_ADDR Close session:$res" "" "Activate"
    return 0
}
function cancelBiosUpdate()
{
    res=`curl -s -X GET --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken"  https://$IP_ADDR/api/biosCancelUpdate --insecure`
    result=`echo $res|grep "error"`
    if [ "$result" != "" ]
    then
        recordLog 2  "$IP_ADDR Failed to cancel BIOS update: $res" "Failed" ""
        return 255
    fi
    recordLog 2 "$IP_ADDR Cancel BIOS update Success:$res" "Failed" ""
    return 0
}
#stop batch update
function stopBatch(){
    if [ ! -e "$STOP_FILE" ]
    then
        touch $STOP_FILE
        recordLog 2  "stop batch update,STOP_FILE:$STOP_FILE" "" ""
    fi
}

function get_update_progress()
{
    res=`curl -s -X GET --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken"  https://$IP_ADDR/api/maintenance/firmware/flash-progress --insecure`
    progress=`echo $res | awk -F 'progress' '{print $2}' | awk -F '\"' '{print $3}'`
    if [ $? -ne 0 ]
    then
        return 255
    fi

    if [ "$progress" == "Complete..." ] || [ "$progress" == "Completed." ] || [ "$progress" == "completed." ] || [ "$progress" == "Success..." ]
    then
        let progress=100
        recordLog 5 "$IP_ADDR BIOS update:${progress} %" "In Progress" "Apply"
        recordLog 2 "$IP_ADDR Update success!" "Finish" "Activate"
        #deleteSession
        break
    else
        progress=`echo $progress | awk -F '%' '{print $1}'`
    fi
    return $progress
}

function flash_node()
{   
    load_and_update $IP_ADDR $USER_NAME $USER_PASSWD $BIN_FILE
    if [ $? -ne 0 ]
    then
       return 255
    fi
    return 0
}

#power reset
function powerResetExec()
{
    if [ "$POWER_RESET"  = "y" ] ;then 
        POWER_STATUS=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD power status 2>&1`
        #echo "$POWER_STATUS"
        if [ "$POWER_STATUS" = "Chassis Power is on" ] ;then
            sleep 30
            powerReset=`curl -s -X POST --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"power_command":"3"}'  https://$IP_ADDR/api/actions/power --insecure`
            result=`echo $powerReset|grep "Error"`
            if [ "$result" != "" ] 
            then
                recordLog 4 "$IP_ADDR Failed to power reset,detail:$powerReset" "Reboot Failed" "Activate"
                deleteSession
                return 255
            fi
        elif [ "$POWER_STATUS" = "Chassis Power is off" ] ;then
            sleep 30
            powerOn=`curl -s -X POST --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"power_command":"1"}'  https://$IP_ADDR/api/actions/power --insecure`
            result=`echo $powerOn|grep "Error"`
            if [ "$result" != "" ] 
            then
                recordLog 4 "$IP_ADDR Failed to power on,detail:$powerOn"  "Reboot Failed" "Activate"
                deleteSession
                return 255
            fi
        else
            recordLog 2 "$IP_ADDR $POWER_STATUS" "In Progress" "Activate"
        fi
        recordLog 2 "$IP_ADDR Power reset success!" "In Progress" "Activate"
    elif [ "$POWER_RESET" = "m" ] ;then
        powerReset=y
        echo "whether to  powerReset ? y or n"
        read -e powerReset
        if [ $powerReset = "y" ] ;then
            POWER_STATUS=`ipmitool -I lanplus -H $IP_ADDR -U $USER_NAME -P $USER_PASSWD power status 2>&1`
            #echo "$POWER_STATUS"
            if [ "$POWER_STATUS" = "Chassis Power is on" ] ;then
                sleep 30
                powerReset=`curl -s -X POST --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"power_command":"3"}'  https://$IP_ADDR/api/actions/power --insecure`
                result=`echo $powerReset|grep "Error"`
                if [ "$result" != "" ] 
                then
                    recordLog 4 "$IP_ADDR Failed to power reset,detail:$powerReset" "Reboot Failed" "Activate"
                    deleteSession
                    return 255
                fi
            elif [ "$POWER_STATUS" = "Chassis Power is off" ] ;then
                sleep 30
                powerOn=`curl -s -X POST --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"power_command":"1"}'  https://$IP_ADDR/api/actions/power --insecure`
                result=`echo $powerOn|grep "Error"`
                if [ "$result" != "" ] 
                then
                    recordLog 4 "$IP_ADDR Failed to power on,detail:$powerOn" "Reboot Failed" "Activate"
                    deleteSession
                    return 255
                fi
            else
                recordLog 2 "$IP_ADDR $POWER_STATUS" "In Progress" "Activate"
            fi
        else
            recordLog 2 "$IP_ADDR Power reset not execute ,please execute manually!" "In Progress" "Activate"
        fi
    else
        recordLog 2 "$IP_ADDR Power reset not execute ,please execute manually!" "In Progress" "Activate"
    fi
    return 0
}

#start 
function load_and_update ()
{    
    #get session
    FAIL_COUNT=0
    for ((i=1; i<=$retrytimes; i++))
    do
        webres=`curl -s --cookie-jar cookies$IP_ADDR -X POST  --data "username=$USER_NAME&password=$USER_PASSWD" https://$IP_ADDR/api/session --insecure`
        result=`echo $webres|grep "error"`
        if [ "$result" != "" ]
        then
            let FAIL_COUNT++
            sleep 10
        else
            CSRFToken=`echo "$webres"|awk -F "CSRFToken" '{print $2}' |awk -F '"' '{print $3}'`
            cookies=`cat cookies$IP_ADDR |grep  QSESSIONID |awk -F "QSESSIONID" '{print $2}'| sed 's/^[ \t]*//g'`
            break
        fi
    done
    if [ $FAIL_COUNT -eq $retrytimes ];then
        recordLog 4  "$IP_ADDR Failure: Failed to get Session CSRFToken and cookies,detail: $webres" "In Progress" "Upload File"
        return 255
    fi
    rm -f cookies$IP_ADDR
    recordLog 2  "$IP_ADDR Success to get session CSRFToken and cookies" "In Progress" "Upload File"
    
    
    #syncmode
    if [ "$SYNCMODE" == "0" ] || [ "$SYNCMODE" == "1" ]
    then
        let FAIL_COUNT=0
        recordLog 2 "$IP_ADDR Begin to set syncmode $SYNCMODE......" "In Progress"  "Upload File"
        for ((i=1; i<=$retrytimes; i++))
        do
            setimage=`curl -s -X PUT --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken" -H "Content-Type:application/json" --data '{"syncmode":"'$SYNCMODE'"}'  https://$IP_ADDR/api/maintenance/hpm/syncmode --insecure`
            result=`echo $setimage|grep "error"`
            if [ "$result" != "" ]
            then
                let FAIL_COUNT++
                sleep 10
            else
                break
            fi
        done
        if [ $FAIL_COUNT -eq $retrytimes ];then
            recordLog 4  "$IP_ADDR Failure: Failed to set syncmode,detail: $setimage" "" "Upload File"
            deleteSession
            return 255
        fi
        recordLog 2 "$IP_ADDR Set sync mode success; result:$setimage" "In Progress"  "Upload File"
    fi   
    
    #upload image file
    let FAIL_COUNT=0
    recordLog 2 "$IP_ADDR Begin to upload image file:$BIN_FILE,please wait......" "In Progress"  "Upload File"
    for ((i=1; i<=$retrytimes; i++))
    do
        firmware=`curl -s -X POST --cookie "QSESSIONID=$cookies; refresh_disable=1" -H "X-CSRFTOKEN:$CSRFToken" -F "fwimage=@$BIN_FILE;filename=$BIN_FILE;"  https://$IP_ADDR/api/maintenance/hpm/firmware --insecure`
        result=`echo $firmware|grep "Error"`
        if [ "$result" != "" ]
        then
            let FAIL_COUNT++
            sleep 30
        else
            break
        fi
    done
    if [ $FAIL_COUNT -eq $retrytimes ];then
        recordLog 4 "$IP_ADDR Failure: Failed to upload File $BIN_FILE,detail:$firmware"  "Upload File"
        deleteSession
        return 255
    fi
    recordLog 2 "$IP_ADDR Success to upload file:$BIN_FILE,result:$firmware" "In Progress"  "Upload File"
    
}

#check log file
function checkLogFile()
{   
    #check LOG_DIR,if not exist mkdir
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
}


#check parameter
function checkParamter()
{
    echo  "$0 $@"
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
        SYNCMODE=${6}
    fi
    getProductSerial
    
    recordLog 2 "$IP_ADDR Select firmware image file=$BIN_FILE" "In Progress" "Upload File"
    if [ ! -f "$BIN_FILE" ]
    then
        recordLog 4  "$IP_ADDR Failure: firmware image file $BIN_FILE Not exist, stop update" ""  "Upload File"
        return 1
    fi
    
    SYNCMODE=$6
    if [ "$SYNCMODE" == "" ]
    then
        SYNCMODE=99
    elif [ "$SYNCMODE" == "1" ] || [ "$SYNCMODE" == "0" ] || [ "$SYNCMODE" == "99" ]
    then
        recordLog 2 "$IP_ADDR sync mode: $SYNCMODE" "In Progress"  "Upload File"
    else
        recordLog 4 "$IP_ADDR Failure: SYNCMODE $SYNCMODE should be 1 or 0;  0-sync,1-not sync" ""  "Upload File"
        printHelp
        return 1
    fi
    return 0
}

#Real update BIOS 
function singleUpdateBIOS()
{
    checkEnv
    checkParamter $@
    if [ $? -ne 0 ]
    then
        recordLog 2 "$IP_ADDR Failure: Parameter Error ,please check" "start"  "Upload File"
        exit 201
    fi
    printToolVersion
    
    
    checkBMCActive
    if [ $? -ne 0 ]
    then
        recordLog 2  "$IP_ADDR Failure: Firmware not updated, BMC not response, please check BMC IP $IP_ADDR, username $USER_NAME, password $USER_PASSWD" ""  "Upload File"
        exit 202
    fi
      
    #get firmware version
    getfwversion       
    
    check_productName_fru
    if [ $? -ne 0 ]
    then
        recordLog 2  "$IP_ADDR Failure: Firmware not updated ,$IP_ADDR Product Name : $PN is not supported" "Unsupported Machine"  "Upload File"
        exit 202
    fi

    if [ "$SUPPORT" = "0" ]
    then
        recordLog 2  "$IP_ADDR Failure: Firmware not updated, Product Name $PN is not supported" "Unsupported Machine"  "Upload File"
        exit 203
    fi   

    recordLog 2 "$IP_ADDR Update start" "start" "Upload File"

    flash_node $IP_ADDR
    if [ $? -ne 0 ]
    then
        exit 204
    fi

    deleteSession

    recordLog 2 "$IP_ADDR Update firmware finished " "Success" "update Success"
    recordLog 3 "$IP_ADDR Update Success" "Success" "update Success"
    exit 0
}

#Real batch update BIOS 
function batUpdateBIOS()
{    
    checkBMCActive
    if [ $? -ne 0 ]
    then
        recordLog 4  "$IP_ADDR Failure: BIOS not updated, BMC not response, please check BMC IP $IP_ADDR, username $USER_NAME, password $USER_PASSWD"
        return 202
    fi
      
    #get firmware version
    getfwversion
    
    check_productName_fru
    if [ $? -ne 0 ]
    then
        return 255
    fi

    if [ "$SUPPORT" = "0" ]
    then
        recordLog 4  "$IP_ADDR Failure: Product Name $PN is not supported"
        return 255
    fi
   
    recordLog 2 "$IP_ADDR Update start"
    sleep 1
    flash_node $IP_ADDR
    if [ $? -ne 0 ]
    then
        return 255
    fi

    powerResetExec
    if [ $? -ne 0 ]
    then
        return 255
    fi
    deleteSession

    recordLog 2 "$IP_ADDR Update BIOS finished "
    recordLog 3 "$IP_ADDR Update Success"
    return 0
}

#batch update bios
function batchUpdate()
{
    checkEnv
    checkLogFile
    printToolVersion
    
    #clear stop file
    if [ -e $STOP_FILE ]
    then
    	rm -f $STOP_FILE
    fi
    
    #configFile exist
    if [ ! -f "$IP_FILE" ]
    then
        echo  "IP_FILE: $IP_FILE Not exist, please check"
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

    tmpFIFO="/tmp/fdscan1"
    #echo "Tmp FIFO file is:$tmpFIFO"
    mkfifo $tmpFIFO
    exec 6<>$tmpFIFO
    rm -f $tmpFIFO

    for ((i=0;i<${currentThreadNum};i++))
    do
        echo >&6
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
            echo "this line is ignore :$LINE"
            continue
        fi
        echo "this line is :$LINE"
        
        IP_ADDR=`echo $LINE |awk -F ',' '{print $1}'`
        USER_NAME=`echo $LINE |awk -F ',' '{print $2}'`
        USER_PASSWD=`echo $LINE |awk -F ',' '{print $3}'`

        if [ "$BIN_FILEA" == "" ]
        then
            BIN_FILE=`echo $LINE  |awk -F ',' '{print $4}'`
        else
            BIN_FILE=$BIN_FILEA
        fi
        
        recordLog 2 "$IP_ADDR Select BIOS image file is $BIN_FILE"
        if [ ! -f "$BIN_FILE" ]
        then
            recordLog 4  "$IP_ADDR Failure: BIOS image upgrade file $BIN_FILE does not exist"
            continue
        fi
        
        
        PRESERVE_SETUP_OPTION=`echo $LINE  |awk -F ',' '{print $5}'`
        if [ "$PRESERVE_SETUP_OPTION" == "" ]
        then
            PRESERVE_SETUP_OPTION=1
        elif  [ "$PRESERVE_SETUP_OPTION" == "0" -o "$PRESERVE_SETUP_OPTION" == "1" ]
        then
            PRESERVE_SETUP_OPTION=$PRESERVE_SETUP_OPTION 
        else
            recordLog 4  "$IP_ADDR Failure: The input preserveOption $PRESERVE_SETUP_OPTION Error, the preserveOption should be 0 or 1"
            continue
        fi
        
        PRESERVE_ME=`echo $LINE  |awk -F ',' '{print $6}'`
        if [ "$PRESERVE_ME" == "" ]
        then
            PRESERVE_ME=0
        elif  [ "$PRESERVE_ME" == "0" -o "$PRESERVE_ME" == "1" ]
        then
            PRESERVE_ME=$PRESERVE_ME    
        else
            recordLog 4  "$IP_ADDR The input preserve_me option $PRESERVE_ME Error, the input should be 1 or 0 "
            continue
        fi
        
        POWER_RESET=`echo $LINE  |awk -F ',' '{print $7}'`
        if [ "$POWER_RESET" == "" ]
        then
            POWER_RESET=n
        elif  [ "$POWER_RESET" == "n" -o "$POWER_RESET" == "y" -o "$POWER_RESET" == "m" ]
        then
            POWER_RESET=$POWER_RESET
        else
            recordLog 4  "$IP_ADDR The input power reset option: $POWER_RESET Error, the input should be n,y or m , please check"
            continue
        fi
        
        
        recordLog 2 "batUpdateBIOS $IP_ADDR $USER_NAME $USER_PASSWD  $BIN_FILE $PRESERVE_SETUP_OPTION $PRESERVE_ME  $POWER_RESET"
        if [ x"$IP_ADDR" != "x" ]
        then
            read -u6
            {
                batUpdateBIOS $IP_ADDR $USER_NAME $USER_PASSWD  $BIN_FILE $PRESERVE_SETUP_OPTION $PRESERVE_ME  $POWER_RESET
                if [ $? -ne 0 ]
                then
                    #recordLog 4 "$IP_ADDR "
                    recordLog 2 ""
                fi
                echo >&6
            } &
        fi    
    }
    done

     
    wait
    recordLog 2 "All BIOS update done"
    exec 6<&-
    exec 6>&-
    exit 0
}


function inBandUpdateBIOS()
{    
    checkLogFile
    printToolVersion
    
    if [ $# -eq 2 ]
    then
        recordLog 2 "$0 $1 $2"
        BIN_FILE=$2
    elif [ $# -eq 3 ]
    then
        recordLog 2 "$0 $1 $2 $3"
        BIN_FILE=$2
        PRESERVE_SETUP_OPTION=$3
    elif [ $# -eq 4 ]
    then
        recordLog 2 "$0 $1 $2 $3 $4"
        BIN_FILE=$2
        PRESERVE_SETUP_OPTION=$3
        PRESERVE_ME=$4
    elif [ $# -eq 5 ]
    then
        recordLog 2 "$0 $1 $2 $3 $4 $5"
        BIN_FILE=$2
        PRESERVE_SETUP_OPTION=$3
        PRESERVE_ME=$4
        POWER_RESET=$5
    else
        echo "The num of parameter $# is wrong! please check "
        printHelp
        exit 1
    fi

    if [ ! -f "$BIN_FILE" ]
    then
        recordLog 2  "BIOS upgrade image file:'$BIN_FILE' Not exist, please check image file"
        exit 1
    fi

    #check preserve setup option
    if [ "$PRESERVE_SETUP_OPTION" == "0"  ] || [ "$PRESERVE_SETUP_OPTION" == "1" ]
    then
        recordLog 2 "Preserve setup option is: $PRESERVE_SETUP_OPTION"
    else
        recordLog 2 "Preserve setup option is not 0 or 1 ,please check"
        printHelp
        exit 1
    fi
    
    #check preserve_me
    if [ "$PRESERVE_ME" == "1" ] || [ "$PRESERVE_ME" == "0" ]
    then
        recordLog 2 "PRESERVE_ME: $PRESERVE_ME"
    else
        recordLog 2 "prserve me option should be 1 or 0, 0-upgrade BIOS+ME; 1-upgrade BIOS"
        printHelp
        exit 1
    fi
    
    #check power reset
    if [ "$POWER_RESET" == "y" ] || [ "$POWER_RESET" == "n" ] || [ "$POWER_RESET" == "m" ]
    then
        recordLog 2 "POWER_RESET: $POWER_RESET"
    else
        recordLog 2 "POWER_RESET should be y,n or m, please check"
        printHelp
        exit 1
    fi
    
    
    # check linux
    if [ `getconf WORD_BIT` -eq 32 ] && [ `getconf LONG_BIT` -eq 64 ] ; then
        AFULNX="afulnx_64"  
    else
        AFULNX="afulnx_32"
    fi
    
    #check AFULNX file
    if [ ! -f "$AFULNX" ]
    then
        recordLog 2  "$IP_ADDR $AFULNX file not exist, please check"
        exit 255
    fi

    if [ "$PRESERVE_SETUP_OPTION" == "0" ]
    then
        #flash bios
        if [ "$PRESERVE_ME" == "0" ]
        then
            #flash bios
            recordLog 2 "Start Flash bios"
            recordLog 2 "./$AFULNX $BIN_FILE /b /p /n /x /k /l /ME"
            ./$AFULNX $BIN_FILE /b /p /n /x /k /l /ME
        else
            #flash bios
            recordLog 2 "Start Flash bios"
            recordLog 2 "./$AFULNX $BIN_FILE /b /p /n /x /k /l "
            ./$AFULNX $BIN_FILE /b /p /n /x /k /l
        fi
    else
        #load ipmi
        modprobe ipmi_si
        if [ $? = 1 ]
        then
            recordLog 2 "failed to modprobe ipmi_si, exit BIOS Update."
        fi
        modprobe ipmi_devintf
        if [ $? = 1 ]
        then
            recordLog 2 "failed to modprobe ipmi_devintf, exit BIOS Update."
        fi
        
        if hash ipmitool 2>/dev/null ; then
            IPMITOOL="ipmitool"
        else
            chmod 777 ipmitool/bin/ipmitool
            IPMITOOL="ipmitool/bin/ipmitool"
        fi
        
        recordLog 2 "$IPMITOOL raw 0x3c 0x4a 0x0b 0x01 0x20 0x00"
        $IPMITOOL raw 0x3c 0x4a 0x0b 0x01 0x20 0x00
        if [ $? = 0 ]
        then
            recordLog 2 "success execute ipmitool raw 0x3c 0x4a 0x0b 0x01 0x20 0x00."
        else
            recordLog 2 "fail to execute ipmitool raw 0x3c 0x4a 0x0b 0x01 0x20 0x00, exit BIOS Update."
            exit 1
        fi
        
        if [ "$PRESERVE_ME" == "0" ]
        then
            #flash bios
            recordLog 2 "Start Flash bios"
            recordLog 2 "./$AFULNX $BIN_FILE /b /p /n /x /k /l /ME"
            ./$AFULNX $BIN_FILE /b /p /n /x /k /l /ME
        else
            #flash bios
            recordLog 2 "Start Flash bios"
            recordLog 2 "./$AFULNX $BIN_FILE /b /p /n /x /k /l "
            ./$AFULNX $BIN_FILE /b /p /n /x /k /l
        fi
    fi

    recordLog 2 "bios update is finish"
    
    
    if [ "$POWER_RESET" == "y" ] ;then
        recordLog 2 "Power reset execute..."
        ./Gobalreset
    elif [ "$POWER_RESET" = "m" ] ;then
        powerReset=y
        echo "whether to  reboot server ? y or n"
        read -e powerReset
        if [ $powerReset = "y" ] ;then
            recordLog 2 "Power reset execute..."
            ./Gobalreset
        else
            recordLog 2 "Power reset not execute ,please execute manually!"
        fi
    else
        recordLog 2 "Power reset not execute ,please execute manually!"
    fi
    exit 0
}


case $1 in

        -h|--help)
            printHelp
            exit
            ;;
        -s|-S|--single)
            #echo "singleUpdateBIOS $@"
            singleUpdateBIOS $@
            exit
            ;;
        *)
            printHelp
            exit
            ;;
esac
