"""
Script to update file_formatter.py with the actual logo base64.
Reads logo_base64.txt and updates the SOCRATE_LOGO_BASE64 variable.
"""

from pathlib import Path

# Paths
LOGO_BASE64_PATH = Path(__file__).parent / "logo_base64.txt"
FORMATTER_PATH = Path(__file__).parent / "file_formatter.py"
BACKUP_PATH = Path(__file__).parent / "file_formatter.py.backup"

def update_formatter_with_logo():
    """Update file_formatter.py with actual logo base64."""
    try:
        print("=" * 60)
        print("🎨 UPDATING FILE FORMATTER WITH LOGO")
        print("=" * 60)
        print()
        
        # Read logo base64
        print(f"📖 Reading logo base64 from: {LOGO_BASE64_PATH}")
        with open(LOGO_BASE64_PATH, 'r') as f:
            logo_base64 = f.read().strip()
        
        print(f"✅ Logo base64 loaded ({len(logo_base64)} characters)")
        
        # Read current formatter
        print(f"📖 Reading formatter from: {FORMATTER_PATH}")
        with open(FORMATTER_PATH, 'r', encoding='utf-8') as f:
            formatter_content = f.read()
        
        # Create backup
        print(f"💾 Creating backup at: {BACKUP_PATH}")
        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            f.write(formatter_content)
        
        # Find and replace the placeholder
        placeholder_start = 'SOCRATE_LOGO_BASE64 = """'
        placeholder_end = '"""'
        
        start_idx = formatter_content.find(placeholder_start)
        if start_idx == -1:
            print("❌ Error: Could not find SOCRATE_LOGO_BASE64 placeholder")
            return False
        
        # Find end of placeholder
        start_idx += len(placeholder_start)
        end_idx = formatter_content.find(placeholder_end, start_idx)
        
        if end_idx == -1:
            print("❌ Error: Could not find end of placeholder")
            return False
        
        # Replace
        print("🔄 Replacing placeholder with actual logo...")
        new_content = (
            formatter_content[:start_idx] +
            '\n' + logo_base64 + '\n' +
            formatter_content[end_idx:]
        )
        
        # Write updated file
        print(f"💾 Writing updated formatter to: {FORMATTER_PATH}")
        with open(FORMATTER_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print()
        print("✅ SUCCESS!")
        print("=" * 60)
        print("📄 file_formatter.py updated with actual logo")
        print("💾 Backup saved as file_formatter.py.backup")
        print("🎨 Logo is now embedded in HTML exports")
        print("=" * 60)
        print()
        print("🔄 Next steps:")
        print("1. Restart the bot: start_bot.bat")
        print("2. Test: /outline → 🌐 Scarica HTML")
        print("3. Open HTML in browser - you should see the logo!")
        print()
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = update_formatter_with_logo()
    
    if not success:
        print("\n❌ Update failed. Check error messages above.")
        print("💡 Make sure logo_base64.txt exists in the same folder.")
    
    input("\nPress Enter to close...")
