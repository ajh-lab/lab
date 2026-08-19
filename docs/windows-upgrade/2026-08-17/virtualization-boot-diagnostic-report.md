# Windows Hypervisor / WSL2 Boot Diagnostic Report

Date: 2026-08-17

## Current State

- Motherboard: ASRock X570M Pro4
- CPU: AMD Ryzen 7 5800X
- BIOS: American Megatrends Inc. P5.67, release date 2025-06-23 / 2025-06-24 as reported by Windows
- Windows: Windows 11 Pro, build 26200.9168, DisplayVersion 25H2
- CPU virtualization as seen by Windows right now: disabled in firmware
- BCD current loader:
  - `hypervisorlaunchtype Auto`
  - `isolatedcontext Yes`
  - `nx OptIn`
  - no explicit `vsmlaunchtype` observed
- Optional Windows features:
  - `VirtualMachinePlatform Enabled`
  - `Microsoft-Windows-Subsystem-Linux Enabled`
  - `HypervisorPlatform Disabled`
  - `Microsoft-Hyper-V-All Disabled`
- WSL:
  - Default distribution: `Ubuntu-22.04`
  - Default WSL version: 2
  - WSL package: 2.1.5.0
  - Distributions are version 2
  - Current launch fails because firmware virtualization and/or hypervisor launch are unavailable
- Docker:
  - Docker CLI is installed
  - Docker Desktop Linux engine pipe is unavailable while WSL2/hypervisor is unavailable

## Evidence

- Known boot matrix before this session:
  - SVM off + hypervisor auto: boots
  - SVM on + hypervisor off: boots
  - SVM on + hypervisor auto: fails into Automatic Repair
- Current boot is using `hypervisorlaunchtype Off`.
- System logs show failed boot status records:
  - 2026-08-17 17:47:53: last boot success status false
  - 2026-08-17 19:55:41: last boot success status false
- Hyper-V-Hypervisor Event 42 is present while SVM is disabled:
  - `Hypervisor launch failed; Either SVM not present or not enabled in BIOS.`
  - This is expected for the current firmware state and is not proof of a broken CPU.
- Kernel-Boot Event 124 is present while SVM/hypervisor are unavailable:
  - VSM not initialized.
- Kernel-Boot Event 153 at 2026-08-17 19:55:41 says VBS policy included `VBS Enabled,VSM Required,Boot Chain Signer Soft Enforced`, then VBS was disabled because the hypervisor was unavailable.
- Startup Repair `SrtTrail.txt` reports no root cause and checks completed successfully.
- No recent minidump was produced for this incident. The only minidump found is from 2026-05-30.
- No WHEA-Logger events were found in the checked window.
- Device Guard / VBS CIM state:
  - `VirtualizationBasedSecurityStatus 0`
  - security services configured/running are `{0}`
  - registry policy path `HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard` is missing
  - `gpresult` shows no configured Administrative Template policy for the computer
- Code Integrity operational log did not show a boot-time driver block tied to the failed boot. It did show unrelated user-mode signing-level failures involving `nvspcap64.dll`, Overwolf, and OBS hook DLLs.
- Third-party / low-level drivers worth tracking:
  - AMD Ryzen Master kernel driver: `AMDRyzenMasterDriverV22`, running, auto start
  - Corsair low-level access drivers, running, auto start
  - SpeedFan kernel driver, running, auto start
  - Logitech CPU temperature driver, running, auto start
  - CPUID driver `cpuz160`, running, demand start
  - BattlEye driver `BEDaisy`, running, demand start
  - VMware `vsock.sys`, running, boot start
  - VirtualBox and most VMware kernel drivers are installed but disabled
- Windows component health:
  - Initial `DISM /ScanHealth`: component store repairable
  - Initial `sfc /scannow`: corrupt files found and repaired
  - CBS log showed corrupt files including `VbsSI_Audit.P7b` and `VbsSI_Audit.xml`, plus many payload/file-flag corruptions
  - After repairs, `DISM /CheckHealth`: no component store corruption detected
  - After repairs, `sfc /verifyonly`: no integrity violations

## Firmware / Chipset

- Installed BIOS: ASRock X570M Pro4 P5.67 beta, 2025-06-23/24, AGESA ComboAM4v2 1.2.0.F per ASRock release notes.
- ASRock lists a newer stable BIOS 5.80 dated 2026-04-07. Its visible release note is Secure Boot key update, not an explicit SVM/AGESA virtualization fix.
- Installed AMD chipset package: `2.11.26.106`, with several component install dates from 2021.
- AMD current X570 chipset package found: `8.08.12.551`, released 2026-08-14.

## Root-Cause Hypothesis

1. Windows component corruption affecting VBS / secure boot firmware update payloads - medium-high confidence. Evidence: DISM/SFC found and repaired corruption, including VBS audit files. The failing configuration is exactly the one that allows hypervisor/VSM initialization.
2. Old AMD chipset / PSP / platform drivers interacting badly with Windows 11 25H2 hypervisor startup - medium confidence. Evidence: installed AMD chipset package is years behind current AMD X570 package, with old PSP/PCI/GPIO components.
3. Low-level hardware monitoring / RGB / tuning drivers conflicting when Hyper-V/VSM initializes - medium confidence. Evidence: AMD Ryzen Master, Corsair low-level access, SpeedFan, Logitech temperature, CPUID, and anti-cheat drivers are present/running. No direct Code Integrity block was found.
4. BIOS/AGESA issue - medium-low confidence. Evidence: SVM itself works when the Windows hypervisor is off, and installed BIOS is fairly recent AGESA 1.2.0.F. A newer ASRock BIOS exists, but its release note does not point directly at virtualization.
5. Full Hyper-V optional feature absence - low confidence. WSL2/Docker need Virtual Machine Platform and the Windows hypervisor, not the full Hyper-V management stack.

## Changes Made

1. Ran `sfc /scannow`.
   - Result: corrupt system files found and repaired.
   - Rollback: no direct rollback; this restores protected Windows files from trusted component sources.
2. Ran `DISM /Online /Cleanup-Image /RestoreHealth` twice.
   - Result: component store corruption was repaired. CBS reports all WCP store corruptions fixed.
   - Rollback: no direct rollback; this repairs the Windows component store from Windows Update/component sources.
3. Ran verification:
   - `DISM /Online /Cleanup-Image /CheckHealth`
   - `sfc /verifyonly`
   - Result: no component store corruption and no SFC integrity violations.
4. Changed BCD `hypervisorlaunchtype` from `Off` to `Auto`.
   - Command: `bcdedit /set {current} hypervisorlaunchtype auto`
   - Reason: required for WSL2/Docker once SVM is enabled; with SVM still disabled this matches the previously known bootable configuration.
   - Rollback: `bcdedit /set {current} hypervisorlaunchtype off`

No BIOS settings, partitions, EFI layout, Secure Boot keys, TPM ownership, optional Windows features, drivers, or software installs/uninstalls were changed.

## Recommended Remediation Order

1. Keep SVM disabled for one normal reboot after the DISM/SFC repairs.
   - Purpose: prove the repaired Windows image boots cleanly before changing firmware state.
2. Confirm one normal boot with `hypervisorlaunchtype Auto` and SVM still disabled.
   - Expected boot result: should boot, matching the already-known passing configuration.
   - Rollback from Windows: `bcdedit /set {current} hypervisorlaunchtype off`
   - Recovery rollback if Windows will not boot: from WinRE Command Prompt, run the same `bcdedit /set {current} hypervisorlaunchtype off`.
3. Enable SVM in BIOS and boot once.
   - This tests the original failing combination after Windows integrity repair.
4. If it boots, validate:
   - `systeminfo`
   - `wsl --status`
   - `wsl -l -v`
   - `wsl --exec uname -a`
   - start Docker Desktop
   - `docker version`
   - `docker info`
   - `docker run --rm hello-world`
5. If it still fails, revert SVM off in BIOS to regain Windows, keep `hypervisorlaunchtype Auto`, and update AMD chipset drivers from AMD before the next SVM test.
   - Reason: the current AMD chipset package is very old relative to the current X570 package.
6. If the chipset update does not fix it, perform a targeted temporary-driver test, one driver family at a time:
   - AMD Ryzen Master driver
   - Corsair low-level access drivers / iCUE
   - SpeedFan
   - Logitech CPU temperature driver
   - BattlEye / anti-cheat drivers
   - VMware `vsock.sys`
7. BIOS update should be considered after chipset and driver isolation.
   - Installed BIOS is recent enough that it is not the first thing to change.
   - ASRock 5.80 is newer stable firmware, but the visible release note points to Secure Boot keys, not an explicit SVM/hypervisor fix.

## Controlled Test Matrix

Known:

- SVM off + hypervisor auto: pass
- SVM on + hypervisor off: pass
- SVM on + hypervisor auto: fail before repair

Next tests:

1. SVM off + hypervisor auto: current next reboot test after repair
2. SVM on + hypervisor auto: test only after confirming test 1
3. If test 2 fails, update AMD chipset drivers and repeat test 2
4. If still failing, isolate one low-level driver family at a time and repeat test 2

## Notes

- The repair evidence is significant because the corrupt files included VBS-related payloads, and the failed boot path is the hypervisor/VSM path.
- Do not enable the full `Microsoft-Hyper-V-All` feature unless a separate workload requires it.
- Do not change partitions, EFI layout, TPM ownership, Secure Boot keys, or reset Windows based on current evidence.

## 2026-08-18 Addendum

After the AMD chipset update and another failed SVM test, Windows is booted again with SVM disabled. Current non-elevated checks show:

- CPU virtualization firmware state: disabled.
- Windows booted normally at 2026-08-18 00:00:43.
- AMD chipset update installed successfully:
  - AMD Chipset Software `8.08.12.551`
  - AMD PSP Driver `5.40.0.0`
  - AMD PCI Driver `1.0.0.90`
  - AMD GPIO2 Driver `2.2.0.136`
  - AMD Ryzen Balanced Driver `8.0.1.13`
  - AMD SMBus Driver `5.12.0.44`
- Latest boot logs still show:
  - Hyper-V-Hypervisor Event 42 while SVM is disabled.
  - Kernel-Boot Event 153: `VBS Enabled,VSM Required,Boot Chain Signer Soft Enforced`.
  - Device Guard CIM and registry policy still say VBS is not configured/running.
- Startup Repair again reported no root cause.
- No recent minidump or WHEA hardware error was found.

The next narrow, reversible test is to keep the Windows hypervisor enabled but disable Virtual Secure Mode launch:

```powershell
bcdedit /enum {current}
bcdedit /set {current} vsmlaunchtype off
bcdedit /enum {current}
```

Applied at 2026-08-18 after confirming elevated PowerShell access:

- `hypervisorlaunchtype Auto`
- `vsmlaunchtype Off`
- before/after BCD output saved to `vsm-bcd-change.log`
- Reboot with SVM still disabled completed successfully at 2026-08-18 00:46:45.
- Post-reboot check confirmed `hypervisorlaunchtype Auto`, `vsmlaunchtype Off`, and `VirtualizationFirmwareEnabled False`.

Rollback:

```powershell
bcdedit /deletevalue {current} vsmlaunchtype
```

If the machine still fails with SVM enabled after `vsmlaunchtype Off`, recover by disabling SVM in BIOS again. The next suspect class after that is low-level kernel drivers, starting with AMD Ryzen Master and hardware monitoring/RGB drivers.

After testing SVM enabled with `vsmlaunchtype Off`, Windows still failed to boot, but WinRE/Startup Repair appeared. Post-recovery checks on 2026-08-18 showed:

- SVM disabled again for recovery.
- `hypervisorlaunchtype Auto`
- `vsmlaunchtype Off`
- `isolatedcontext Yes`
- latest Startup Repair log still reported `Number of root causes = 0`
- no recent minidump was created

Next BCD isolation change applied:

```powershell
bcdedit /set {current} isolatedcontext no
```

Current test state:

- `hypervisorlaunchtype Auto`
- `vsmlaunchtype Off`
- `isolatedcontext No`

Before/after output saved to `isolatedcontext-bcd-change.log`.

Rollback:

```powershell
bcdedit /set {current} isolatedcontext yes
```

If SVM still fails in this state, the next reversible BCD-only test should be:

```powershell
bcdedit /set {current} hypervisoriommupolicy disable
```

Rollback:

```powershell
bcdedit /deletevalue {current} hypervisoriommupolicy
```

Follow-up: the IOMMU policy test did not allow Windows to boot with SVM enabled. It was rolled back on 2026-08-18:

```powershell
bcdedit /deletevalue {current} hypervisoriommupolicy
```

Next driver isolation test applied on 2026-08-18:

```powershell
sc.exe config AMDRyzenMasterDriverV22 start= disabled
```

State after the change:

- `hypervisorlaunchtype Auto`
- `vsmlaunchtype Off`
- `isolatedcontext Yes`
- `hypervisoriommupolicy` removed
- `AMDRyzenMasterDriverV22` startup changed from `AUTO_START` to `DISABLED`

The Ryzen Master driver remains loaded in the current Windows session until reboot, but it should not load on the next boot.

Before/after output saved to `amd-ryzenmaster-driver-isolation-change.log`.

Rollback:

```powershell
sc.exe config AMDRyzenMasterDriverV22 start= auto
```

Follow-up: the `isolatedcontext No` test did not boot cleanly even with SVM disabled. It was rolled back on 2026-08-18:

```powershell
bcdedit /set {current} isolatedcontext yes
```

Current BCD state after rollback:

- `hypervisorlaunchtype Auto`
- `vsmlaunchtype Off`
- `isolatedcontext Yes`

Before/after output saved to `isolatedcontext-rollback.log`.

IOMMU policy test applied on 2026-08-18:

```powershell
bcdedit /set {current} hypervisoriommupolicy disable
```

Current BCD state:

- `hypervisorlaunchtype Auto`
- `hypervisoriommupolicy Disable`
- `vsmlaunchtype Off`
- `isolatedcontext Yes`

Before/after output saved to `hypervisoriommupolicy-bcd-change.log`.

Rollback:

```powershell
bcdedit /deletevalue {current} hypervisoriommupolicy
```
