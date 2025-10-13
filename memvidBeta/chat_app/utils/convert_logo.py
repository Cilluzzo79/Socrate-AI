"""
Script to convert Socrate AI logo to base64 for embedding in HTML.
"""

import base64
from pathlib import Path

# Path to logo
LOGO_PATH = Path(__file__).parent.parent.parent / "Socrate scritta.png"
OUTPUT_PATH = Path(__file__).parent / "logo_base64.txt"

def convert_logo_to_base64():
    """Convert logo image to base64 string."""
    try:
        print(f"Reading logo from: {LOGO_PATH}")
        
        # Read image file
        with open(LOGO_PATH, 'rb') as image_file:
            logo_bytes = image_file.read()
        
        # Convert to base64
        logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
        
        # Save to file
        with open(OUTPUT_PATH, 'w') as output_file:
            output_file.write(logo_base64)
        
        print(f"✅ Logo converted successfully!")
        print(f"📄 Base64 saved to: {OUTPUT_PATH}")
        print(f"📊 Size: {len(logo_base64)} characters")
        print(f"📊 Original size: {len(logo_bytes)} bytes")
        
        # Show preview
        preview = logo_base64[:100] + "..." + logo_base64[-100:]
        print(f"\n📋 Preview:\n{preview}\n")
        
        return logo_base64
        
    except FileNotFoundError:
        print(f"❌ Error: Logo file not found at {LOGO_PATH}")
        return None
    except Exception as e:
        print(f"❌ Error converting logo: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("🎨 SOCRATE AI LOGO CONVERTER")
    print("=" * 60)
    print()
    
    result = convert_logo_to_base64()
    
    if result:
        print("\n✅ Success! Now you can use the base64 in HTML.")
        print("💡 The base64 string is saved in 'logo_base64.txt'")
    else:
        print("\n❌ Conversion failed. Check the error messages above.")
    
    print("\n" + "=" * 60)
