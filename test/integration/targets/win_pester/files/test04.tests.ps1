Param(
    $Service,
    $Process
)

Describe "Process should exist" {
    it "Process $Process should be running" -Skip:([String]::IsNullOrEmpty($Process)) {
        Get-Process -Name $Process -ErrorAction SilentlyContinue | Should Not BeNullOrEmpty
    }
}



Describe "Service should exist" -tag Service {
    it "Service $Service should exist" -Skip:([String]::IsNullOrEmpty($Service)) {
        Get-Service -Name $Service -ErrorAction SilentlyContinue | Should Not BeNullOrEmpty
    }
}
