Param(
    $Service,
    $Process
)

Describe "Process should exist" {
    it "Process $Process should be running" {
        Get-Process -Name $Process -ErrorAction SilentlyContinue| Should -Not -BeNullOrEmpty
    }
}

Describe "Service should exist" -tag Service {
    it "Service $Service should exist" {
        Get-Service -Name $Service-ErrorAction SilentlyContinue | Should -Not -BeNullOrEmpty
    }
}