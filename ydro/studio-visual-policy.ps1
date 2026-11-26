# Pure policy for local preview. A visual score never overrides a failed build/audit.
[CmdletBinding()]
param([switch]$SelfTest)

function Get-StudioVisualOutcome([int]$Code, $Review) {
    $outcome=@{status='unavailable';score=$null;threshold=85}
    if ($null -eq $Review) { return $outcome }
    if ($Code -eq 0 -and $Review.passed -eq $true -and
        $Review.status -eq 'passed' -and $Review.technical_passed -eq $true -and
        $Review.devices.desktop.passed -eq $true -and $Review.devices.mobile.passed -eq $true) {
        $outcome.status='passed'
    } elseif ($Code -eq 2 -and $Review.status -eq 'needs_revision' -and
              $Review.passed -eq $false -and $Review.technical_passed -eq $true) {
        $outcome.status='needs_revision'
    }
    if ($outcome.status -ne 'unavailable') {
        $score=$Review.score
        if (($score -is [int] -or $score -is [long]) -and $score -ge 0 -and $score -le 100) {
            $outcome.score=[int]$score
        } else {
            $outcome.status='unavailable'
        }
    }
    if ($outcome.status -eq 'passed' -and $outcome.score -lt $outcome.threshold) {
        $outcome.status='unavailable'
        $outcome.score=$null
    }
    return $outcome
}

if ($SelfTest) {
    $devices=@{desktop=@{passed=$true};mobile=@{passed=$true}}
    $review=@{status='passed';passed=$true;technical_passed=$true;score=90;devices=$devices}
    if ((Get-StudioVisualOutcome 0 $review).status -ne 'passed') { throw 'Expected visual pass' }
    $review.status='needs_revision';$review.passed=$false;$review.score=62
    $draft=Get-StudioVisualOutcome 2 $review
    if ($draft.status -ne 'needs_revision' -or $draft.score -ne 62) { throw 'Expected scored draft' }
    if ((Get-StudioVisualOutcome 1 $null).status -ne 'unavailable') { throw 'Expected unavailable critic' }
    $review.status='passed';$review.passed=$true;$review.score=90;$devices.mobile.passed=$false
    if ((Get-StudioVisualOutcome 0 $review).status -ne 'unavailable') { throw 'Incomplete review must not pass' }
    $devices.mobile.passed=$true;$review.score=62
    if ((Get-StudioVisualOutcome 0 $review).status -ne 'unavailable') { throw 'Below threshold must not pass' }
    Write-Host 'STUDIO_VISUAL_POLICY_TESTS_PASSED: 5'
}
