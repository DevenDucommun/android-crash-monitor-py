#!/usr/bin/env python3
"""
Automated Problem Resolution System
Safely applies common fixes for Android device issues
"""

import subprocess
import time
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class FixResult:
    """Result of applying an automated fix"""
    success: bool
    message: str
    applied_fixes: List[str]
    warnings: List[str] = None
    errors: List[str] = None

class AutoFixManager:
    """Manages automated fixes for common Android problems"""
    
    def __init__(self):
        self.safe_fixes = {
            'clear_app_cache': {
                'description': 'Clear app caches to free up space and fix corruption',
                'safety': 'safe',  # Safe - doesn't delete user data
                'command_template': 'adb shell pm clear --cache {package}',
                'applies_to': ['app_crash', 'storage_issues', 'performance']
            },
            
            'restart_adb': {
                'description': 'Restart ADB connection to fix communication issues',
                'safety': 'safe',
                'commands': ['adb kill-server', 'adb start-server'],
                'applies_to': ['connection_issues', 'device_not_found']
            },
            
            'clear_system_cache_partition': {
                'description': 'Clear system cache partition (safe, non-destructive)',
                'safety': 'safe',
                'command': 'adb shell recovery --wipe_cache',
                'applies_to': ['system_instability', 'performance_issues'],
                'requires_recovery': True  # Needs device in recovery mode
            },
            
            'force_stop_app': {
                'description': 'Force stop problematic apps',
                'safety': 'safe',
                'command_template': 'adb shell am force-stop {package}',
                'applies_to': ['app_hanging', 'memory_issues']
            },
            
            'disable_problematic_app': {
                'description': 'Temporarily disable apps causing crashes',
                'safety': 'reversible',  # Can be undone
                'command_template': 'adb shell pm disable-user {package}',
                'undo_template': 'adb shell pm enable {package}',
                'applies_to': ['repeated_crashes', 'system_instability']
            },
            
            'clear_downloads_cache': {
                'description': 'Clear Downloads app cache and temporary files',
                'safety': 'safe',
                'commands': [
                    'adb shell pm clear com.android.providers.downloads',
                    'adb shell rm -rf /sdcard/Android/data/*/cache/*'
                ],
                'applies_to': ['storage_full', 'download_issues']
            },
            
            'fix_permissions': {
                'description': 'Reset app permissions to defaults',
                'safety': 'user_prompt',  # Ask user before applying
                'command_template': 'adb shell pm reset-permissions {package}',
                'applies_to': ['permission_errors', 'app_crashes']
            },
            
            'clear_dalvik_cache': {
                'description': 'Clear Dalvik/ART cache (requires reboot)',
                'safety': 'requires_reboot',
                'command': 'adb shell rm -rf /data/dalvik-cache/*',
                'applies_to': ['app_crashes', 'system_instability', 'performance']
            }
        }
        
        self.problem_patterns = {
            'database_corruption': ['clear_app_cache', 'restart_adb'],
            'out_of_memory': ['clear_app_cache', 'force_stop_app'],
            'storage_full': ['clear_app_cache', 'clear_downloads_cache'],
            'app_crash': ['clear_app_cache', 'force_stop_app', 'fix_permissions'],
            'permission_denied': ['fix_permissions'],
            'hardware_failure': ['restart_adb'],  # Limited options for hardware
            'system_service_crash': ['clear_system_cache_partition', 'clear_dalvik_cache'],
            'network_issues': ['restart_adb']  # Limited fixes available via ADB
        }
    
    def check_device_connection(self) -> bool:
        """Verify device is connected and responsive"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                devices = [line for line in lines if '\tdevice' in line]
                return len(devices) > 0
            return False
        except:
            return False
    
    def is_fix_safe(self, fix_id: str) -> bool:
        """Check if a fix is safe to apply automatically"""
        fix = self.safe_fixes.get(fix_id, {})
        safety = fix.get('safety', 'unsafe')
        return safety in ['safe', 'reversible']
    
    def get_applicable_fixes(self, problem_types: List[str]) -> List[str]:
        """Get list of fixes applicable to the detected problems"""
        applicable_fixes = set()
        
        for problem_type in problem_types:
            fixes = self.problem_patterns.get(problem_type, [])
            applicable_fixes.update(fixes)
        
        # Filter to safe fixes only
        safe_fixes = [fix_id for fix_id in applicable_fixes 
                     if self.is_fix_safe(fix_id)]
        
        return safe_fixes
    
    def apply_fix(self, fix_id: str, package_name: str = None) -> FixResult:
        """Apply a specific fix"""
        if not self.check_device_connection():
            return FixResult(
                success=False,
                message="Device not connected or not responsive",
                applied_fixes=[],
                errors=["No device connection"]
            )
        
        fix = self.safe_fixes.get(fix_id)
        if not fix:
            return FixResult(
                success=False,
                message=f"Unknown fix: {fix_id}",
                applied_fixes=[],
                errors=[f"Fix {fix_id} not found"]
            )
        
        applied_fixes = []
        warnings = []
        errors = []
        
        try:
            # Handle different command formats
            if 'commands' in fix:
                # Multiple commands
                for cmd in fix['commands']:
                    result = subprocess.run(cmd.split(), capture_output=True, 
                                          text=True, timeout=30)
                    if result.returncode == 0:
                        applied_fixes.append(cmd)
                    else:
                        errors.append(f"Command failed: {cmd} - {result.stderr}")
                        
            elif 'command_template' in fix:
                # Template command requiring package name
                if not package_name:
                    return FixResult(
                        success=False,
                        message=f"Fix {fix_id} requires package name",
                        applied_fixes=[],
                        errors=["Package name required but not provided"]
                    )
                
                cmd = fix['command_template'].format(package=package_name)
                result = subprocess.run(cmd.split(), capture_output=True, 
                                      text=True, timeout=30)
                if result.returncode == 0:
                    applied_fixes.append(cmd)
                else:
                    errors.append(f"Command failed: {cmd} - {result.stderr}")
                    
            elif 'command' in fix:
                # Single command
                cmd = fix['command']
                result = subprocess.run(cmd.split(), capture_output=True, 
                                      text=True, timeout=30)
                if result.returncode == 0:
                    applied_fixes.append(cmd)
                else:
                    errors.append(f"Command failed: {cmd} - {result.stderr}")
            
            success = len(applied_fixes) > 0 and len(errors) == 0
            
            # Add warnings for special cases
            if fix.get('requires_reboot'):
                warnings.append("Device reboot recommended for changes to take effect")
            
            if fix.get('requires_recovery'):
                warnings.append("This fix requires device to be in recovery mode")
            
            message = fix['description']
            if success:
                message += " - Applied successfully"
            elif errors:
                message += " - Failed with errors"
            else:
                message += " - No changes made"
            
            return FixResult(
                success=success,
                message=message,
                applied_fixes=applied_fixes,
                warnings=warnings,
                errors=errors
            )
            
        except subprocess.TimeoutExpired:
            return FixResult(
                success=False,
                message=f"Fix {fix_id} timed out",
                applied_fixes=applied_fixes,
                errors=["Command timed out"]
            )
        except Exception as e:
            return FixResult(
                success=False,
                message=f"Fix {fix_id} failed: {str(e)}",
                applied_fixes=applied_fixes,
                errors=[str(e)]
            )
    
    def get_problematic_packages(self) -> List[str]:
        """Get list of apps that might be causing issues"""
        try:
            # Get list of recently crashed apps (simplified)
            result = subprocess.run(['adb', 'logcat', '-d', '-b', 'crash'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Extract package names from crash logs
                packages = set()
                for line in result.stdout.split('\n'):
                    # Look for package names in crash logs
                    match = re.search(r'Process: ([a-zA-Z0-9_.]+)', line)
                    if match:
                        packages.add(match.group(1))
                
                return list(packages)[:5]  # Return top 5 problematic packages
            
            return []
        except:
            return []
    
    def apply_safe_fixes_automatically(self, problem_types: List[str]) -> Dict[str, FixResult]:
        """Apply all safe fixes for the given problem types"""
        
        if not self.check_device_connection():
            return {
                'connection_error': FixResult(
                    success=False,
                    message="Device not connected",
                    applied_fixes=[],
                    errors=["No device connection"]
                )
            }
        
        # Get applicable fixes
        fixes_to_apply = self.get_applicable_fixes(problem_types)
        
        # Get problematic packages for targeted fixes
        problematic_packages = self.get_problematic_packages()
        
        results = {}
        
        for fix_id in fixes_to_apply:
            fix = self.safe_fixes[fix_id]
            
            # Apply fix with or without package name
            if 'command_template' in fix and problematic_packages:
                # Apply to each problematic package
                for package in problematic_packages:
                    result_key = f"{fix_id}_{package}"
                    results[result_key] = self.apply_fix(fix_id, package)
            else:
                # Apply fix without package name
                results[fix_id] = self.apply_fix(fix_id)
        
        return results
    
    def create_fix_report(self, results: Dict[str, FixResult]) -> str:
        """Create a user-friendly report of applied fixes"""
        
        if not results:
            return "No fixes were applied."
        
        successful_fixes = [k for k, v in results.items() if v.success]
        failed_fixes = [k for k, v in results.items() if not v.success]
        
        report = "🔧 **Automatic Fix Report**\n\n"
        
        if successful_fixes:
            report += f"✅ **Successfully Applied ({len(successful_fixes)} fixes):**\n"
            for fix_id in successful_fixes:
                result = results[fix_id]
                report += f"• {result.message}\n"
                if result.warnings:
                    for warning in result.warnings:
                        report += f"  ⚠️ {warning}\n"
            report += "\n"
        
        if failed_fixes:
            report += f"❌ **Failed to Apply ({len(failed_fixes)} fixes):**\n"
            for fix_id in failed_fixes:
                result = results[fix_id]
                report += f"• {result.message}\n"
                if result.errors:
                    for error in result.errors:
                        report += f"  💥 {error}\n"
            report += "\n"
        
        # Add general recommendations
        report += "**Next Steps:**\n"
        report += "• Restart your device to ensure all changes take effect\n"
        report += "• Test your apps to see if issues are resolved\n"
        report += "• If problems persist, consider manual troubleshooting\n"
        
        return report

def create_simple_auto_fixer() -> 'AutoFixManager':
    """Create an auto-fixer instance with safe, non-destructive fixes only"""
    fixer = AutoFixManager()
    
    # Remove any potentially risky fixes for simple mode
    risky_fixes = ['clear_dalvik_cache', 'disable_problematic_app']
    for risky_fix in risky_fixes:
        if risky_fix in fixer.safe_fixes:
            fixer.safe_fixes[risky_fix]['safety'] = 'user_prompt'
    
    return fixer

# Example usage functions
def quick_device_cleanup() -> Dict[str, FixResult]:
    """Perform a quick, safe cleanup of the device"""
    fixer = create_simple_auto_fixer()
    
    # Apply common cleanup fixes
    cleanup_problems = ['storage_full', 'app_crash', 'out_of_memory']
    return fixer.apply_safe_fixes_automatically(cleanup_problems)

def emergency_device_stabilization() -> Dict[str, FixResult]:
    """Apply emergency fixes for unstable devices"""
    fixer = create_simple_auto_fixer()
    
    # Apply stability fixes
    stability_problems = ['system_service_crash', 'out_of_memory', 'app_crash']
    return fixer.apply_safe_fixes_automatically(stability_problems)