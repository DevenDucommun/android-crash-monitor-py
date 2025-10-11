#!/usr/bin/env python3
"""
Plain Language Explainer for Android Crash Monitor
Converts technical crash information into easy-to-understand explanations
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PlainExplanation:
    """A plain-language explanation of a technical problem"""
    problem: str           # What's wrong in simple terms
    why: str              # Why this is happening  
    impact: str           # How this affects the user
    urgency: str          # How urgent this is (High/Medium/Low)
    solutions: List[str]  # Step-by-step fixes in plain language
    technical_note: Optional[str] = None  # Optional technical details

class PlainLanguageExplainer:
    """Converts technical crash data into user-friendly explanations"""
    
    def __init__(self):
        self.crash_patterns = {
            # Database and storage issues
            'database_corruption': {
                'keywords': ['database', 'sqlite', 'corruption', 'db_lock', 'database_disk_image'],
                'explanation': PlainExplanation(
                    problem="Your phone's storage system has become corrupted",
                    why="Apps saved information incorrectly or your device ran out of space",
                    impact="Apps may crash, lose data, or work slowly",
                    urgency="High",
                    solutions=[
                        "Clear storage space (delete old photos, apps, downloads)",
                        "Restart your device to reset the storage system",
                        "Clear app data for problematic apps (Settings > Apps > [App Name] > Storage > Clear Data)",
                        "If problems persist, back up your data and consider a factory reset"
                    ]
                )
            },
            
            # Memory issues
            'out_of_memory': {
                'keywords': ['OutOfMemoryError', 'memory', 'heap', 'allocation failed'],
                'explanation': PlainExplanation(
                    problem="Your device is running out of memory",
                    why="Too many apps are open or an app is using too much memory",
                    impact="Apps will crash and your device may become slow or unresponsive",
                    urgency="High",
                    solutions=[
                        "Close apps you're not using (recent apps button, swipe up on apps)",
                        "Restart your device to free up memory",
                        "Uninstall apps you don't need",
                        "Clear cache for heavy apps (Settings > Apps > [App Name] > Storage > Clear Cache)"
                    ]
                )
            },
            
            # Network connectivity
            'network_issues': {
                'keywords': ['network', 'connection', 'timeout', 'unreachable', 'no_network'],
                'explanation': PlainExplanation(
                    problem="Your device is having trouble connecting to the internet",
                    why="WiFi is unstable, mobile data is weak, or network settings are wrong",
                    impact="Apps can't load content, sync data, or work properly online",
                    urgency="Medium",
                    solutions=[
                        "Check your WiFi connection - try other devices on the same network",
                        "Toggle WiFi off and on (Settings > WiFi > Off > On)",
                        "Try mobile data if available",
                        "Restart your router/modem if at home",
                        "Reset network settings (Settings > System > Reset > Reset Network Settings)"
                    ]
                )
            },
            
            # App permissions
            'permission_denied': {
                'keywords': ['permission', 'denied', 'security', 'access_denied'],
                'explanation': PlainExplanation(
                    problem="An app doesn't have permission to access something it needs",
                    why="You denied permission or the app lost access due to a system update",
                    impact="App features may not work (camera, location, storage, etc.)",
                    urgency="Medium",
                    solutions=[
                        "Go to Settings > Apps > [App Name] > Permissions",
                        "Turn on permissions the app needs (Camera, Location, Storage, etc.)",
                        "Some apps need 'All the time' location access to work properly",
                        "Restart the app after changing permissions"
                    ]
                )
            },
            
            # Hardware issues
            'hardware_failure': {
                'keywords': ['hardware', 'sensor', 'camera', 'failed', 'not_available', 'service_died'],
                'explanation': PlainExplanation(
                    problem="A hardware component in your device isn't working properly",
                    why="Physical damage, wear and tear, or a system glitch",
                    impact="Features like camera, GPS, or sensors may not work",
                    urgency="High",
                    solutions=[
                        "Restart your device to reset hardware connections",
                        "Check if the problem happens in multiple apps",
                        "Update your device software (Settings > System Update)",
                        "If the problem persists, contact your device manufacturer or visit a repair shop"
                    ]
                )
            },
            
            # System services
            'system_service_crash': {
                'keywords': ['system_service', 'service_died', 'binder', 'system_server'],
                'explanation': PlainExplanation(
                    problem="A core system service on your device has crashed",
                    why="System overload, corrupted system files, or buggy system update",
                    impact="Your device may become unstable, slow, or unresponsive",
                    urgency="High",
                    solutions=[
                        "Restart your device immediately",
                        "If crashes continue, boot in Safe Mode (hold power button, long-press 'Power off')",
                        "Uninstall recently installed apps",
                        "Clear system cache (varies by device - search '[Your Device] clear system cache')",
                        "Consider a factory reset if problems persist"
                    ]
                )
            },
            
            # App crashes
            'app_crash': {
                'keywords': ['NullPointerException', 'RuntimeException', 'crash', 'force close'],
                'explanation': PlainExplanation(
                    problem="An app has crashed due to a programming error",
                    why="Bug in the app, corrupted app data, or incompatibility with your device",
                    impact="The app stops working and may lose unsaved data",
                    urgency="Medium",
                    solutions=[
                        "Force close the app and restart it",
                        "Clear the app's cache (Settings > Apps > [App Name] > Storage > Clear Cache)",
                        "Update the app from the Google Play Store",
                        "If crashes continue, clear app data (you may lose app settings)",
                        "Contact the app developer or try an alternative app"
                    ]
                )
            },
            
            # Storage issues
            'storage_full': {
                'keywords': ['storage', 'space', 'disk_full', 'no_space'],
                'explanation': PlainExplanation(
                    problem="Your device is running out of storage space",
                    why="Too many photos, videos, apps, or downloaded files",
                    impact="Apps can't save data, updates fail, and device performance suffers",
                    urgency="High",
                    solutions=[
                        "Delete old photos and videos (back them up to cloud first)",
                        "Uninstall apps you don't use",
                        "Clear app caches (Settings > Storage > Cached data > Clear)",
                        "Move photos/videos to cloud storage (Google Photos, iCloud, etc.)",
                        "Delete downloaded files and old WhatsApp media"
                    ]
                )
            }
        }
    
    def explain_crash_pattern(self, crash_text: str, crash_type: str = None) -> PlainExplanation:
        """Convert a crash or error into plain language explanation"""
        
        # Convert to lowercase for pattern matching
        text_lower = crash_text.lower()
        
        # Find the best matching pattern
        best_match = None
        max_matches = 0
        
        for pattern_name, pattern_data in self.crash_patterns.items():
            matches = sum(1 for keyword in pattern_data['keywords'] 
                         if keyword.lower() in text_lower)
            
            if matches > max_matches:
                max_matches = matches
                best_match = pattern_name
        
        # Return specific explanation if we found a good match
        if best_match and max_matches > 0:
            explanation = self.crash_patterns[best_match]['explanation']
            # Add technical note with original error
            explanation.technical_note = f"Technical details: {crash_text[:200]}..."
            return explanation
        
        # Fallback generic explanation
        return PlainExplanation(
            problem="Your device encountered an unexpected error",
            why="This could be due to a software bug, system conflict, or resource issue",
            impact="Some apps or features may not work properly",
            urgency="Medium",
            solutions=[
                "Restart your device to clear temporary issues",
                "Make sure your apps are updated",
                "Free up some storage space",
                "If problems continue, note when they happen and contact support"
            ],
            technical_note=f"Technical details: {crash_text[:200]}..."
        )
    
    def generate_device_health_summary(self, crash_count: int, 
                                     critical_patterns: int,
                                     timeframe: str = "recent") -> str:
        """Generate a plain-language device health summary"""
        
        if crash_count == 0:
            return f"""
🌟 **Great News!** Your device looks healthy.

No crashes or serious errors detected in {timeframe} monitoring. 
Your phone is running smoothly! Keep it that way by:
• Regularly restarting your device
• Keeping apps updated  
• Not letting storage get too full
"""
        
        if critical_patterns > 5 or crash_count > 100:
            urgency = "URGENT"
            emoji = "🚨"
            advice = """
**Immediate Action Needed:**
1. Restart your device right now
2. Back up important data immediately
3. Free up storage space
4. Consider visiting a phone repair shop"""
        elif critical_patterns > 2 or crash_count > 20:
            urgency = "HIGH PRIORITY"
            emoji = "⚠️"
            advice = """
**Action Recommended Soon:**
1. Restart your device today
2. Clear app caches and free up space
3. Check for app updates
4. Monitor for more issues"""
        elif crash_count > 5:
            urgency = "MONITOR CLOSELY"
            emoji = "⚠️"
            advice = """
**Keep an Eye On This:**
1. Restart your device when convenient
2. Note if problems get worse
3. Check for software updates"""
        else:
            urgency = "MINOR ISSUES"
            emoji = "ℹ️"
            advice = """
**Minor Issues Detected:**
1. Normal occasional glitches
2. No immediate action needed
3. Keep monitoring"""
        
        return f"""
{emoji} **Device Health Status: {urgency}**

Found {crash_count} issues in {timeframe} monitoring.
{critical_patterns} of these are serious patterns that need attention.

{advice}

**What This Means:**
Your phone is experiencing some problems that could affect performance 
and reliability. The good news is that most phone issues can be fixed 
with simple steps!
"""

    def create_simple_action_plan(self, explanations: List[PlainExplanation]) -> str:
        """Create a prioritized, simple action plan"""
        
        if not explanations:
            return "✅ No action needed - your device is working well!"
        
        # Prioritize by urgency
        urgent = [e for e in explanations if e.urgency == "High"]
        medium = [e for e in explanations if e.urgency == "Medium"] 
        low = [e for e in explanations if e.urgency == "Low"]
        
        action_plan = "🔧 **Simple Fix Plan**\n\n"
        
        if urgent:
            action_plan += "**🚨 Do This First (Important!):**\n"
            for i, explanation in enumerate(urgent[:3], 1):  # Top 3 urgent items
                action_plan += f"{i}. {explanation.problem}\n"
                action_plan += f"   → {explanation.solutions[0]}\n\n"
        
        if medium:
            action_plan += "**⚠️ Then Do This When You Can:**\n"
            for i, explanation in enumerate(medium[:2], 1):  # Top 2 medium items
                action_plan += f"{i}. {explanation.problem}\n"
                action_plan += f"   → {explanation.solutions[0]}\n\n"
        
        action_plan += "**💡 General Advice:**\n"
        action_plan += "• Restart your phone at least once a week\n"
        action_plan += "• Keep 10-20% of your storage free\n"
        action_plan += "• Update apps when you get notifications\n"
        action_plan += "• If problems get worse, back up your data\n"
        
        return action_plan

def convert_technical_report_to_plain_language(technical_report: dict) -> str:
    """Convert a full technical analysis report to plain language"""
    
    explainer = PlainLanguageExplainer()
    
    # Extract key information
    crash_count = technical_report.get('total_crashes', 0)
    critical_patterns = len(technical_report.get('critical_patterns', {}))
    
    # Start with health summary
    health_summary = explainer.generate_device_health_summary(
        crash_count, critical_patterns
    )
    
    # Get explanations for critical patterns
    explanations = []
    critical_patterns_data = technical_report.get('critical_patterns', {})
    
    for pattern_name, pattern_data in critical_patterns_data.items():
        # Get some sample crash text
        sample_crash = ""
        if isinstance(pattern_data, dict) and 'examples' in pattern_data:
            examples = pattern_data['examples']
            if examples:
                sample_crash = str(examples[0])
        
        explanation = explainer.explain_crash_pattern(sample_crash, pattern_name)
        explanations.append(explanation)
    
    # Create action plan
    action_plan = explainer.create_simple_action_plan(explanations)
    
    # Combine everything
    plain_report = f"""
# 📱 Your Phone's Health Report

{health_summary}

{action_plan}

---

**Need Help?**
• This report was generated automatically
• If you don't understand something, ask someone tech-savvy to help
• Contact your phone manufacturer if hardware issues persist
• Back up your important data regularly

**Report Generated:** {technical_report.get('timestamp', 'Unknown')}
"""
    
    return plain_report