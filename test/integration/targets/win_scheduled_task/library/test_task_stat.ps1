#!powershell
#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$params = Parse-Args -arguments $args
$path = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true
$name = Get-AnsibleParam -obj $params -name "name" -type "str"

$result = @{
    changed = $false
}

$service = New-Object -ComObject Schedule.Service
$service.Connect()

try {
    $task_folder = $service.GetFolder($path)
    $result.folder_exists = $true
} catch {
    $result.folder_exists = $false
    $task_folder = $null
}

$folder_tasks = $task_folder.GetTasks(1)
$folder_task_names = @()
$folder_task_count = 0
$task = $null
for ($i = 1; $i -le $folder_tasks.Count; $i++) {
    $task_name = $folder_tasks.Item($i).Name
    $folder_task_names += $task_name
    $folder_task_count += 1

    if ($name -ne $null -and $task_name -eq $name) {
        $task = $folder_tasks.Item($i)
    }
}
$result.folder_task_names = $folder_task_names
$result.folder_task_count = $folder_task_count

if ($name -ne $null) {
    if ($task -ne $null) {
        $task_definition = $task.Definition
        $result.task_exists = $true
        $result.task = @{}

        $properties = @("principal", "registration_info", "settings")
        $collection_properties = @("actions", "triggers")

        foreach ($property in $properties) {
            $property_name = $property -replace "_"
            $result.task.$property = @{}
            $values = $task_definition.$property_name
            Get-Member -InputObject $values -MemberType Property | % {
                # the UserId and GroupID property is represented differently on
                # each Server OS version, convert to SID and back to get the
                # same name for tests
                $value = $values.$($_.Name)
                if ($property_name -eq "principal" -and $_.Name -in @("UserId", "GroupId") -and $value -ne $null) {
                    $sid = Convert-ToSID -account_name $value
                    $value = Convert-FromSid -sid $sid
                }
                $result.task.$property.$($_.Name) = $value
            }
        }

        foreach ($property in $collection_properties) {
            $result.task.$property = @()
            $collection = $task_definition.$property
            $collection_count = $collection.Count
            for ($i = 1; $i -le $collection_count; $i++) {
                $item = $collection.Item($i)
                $item_info = @{}

                Get-Member -InputObject $item -MemberType Property | % {
                    $item_info.$($_.Name) = $item.$($_.Name)
                }
                $result.task.$property += $item_info
            }
        }
    } else {
        $result.task_exists = $false
    }
}

Exit-Json -obj $result
