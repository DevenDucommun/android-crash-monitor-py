#!/usr/bin/env python3
"""
Create a simple app icon for Android Crash Monitor
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """Create a simple app icon"""
    
    # Create different sizes for the icon
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    images = []
    
    for size in sizes:
        # Create image with rounded rectangle background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Background gradient (simulating Android green)
        margin = size // 20
        draw.rounded_rectangle(
            [margin, margin, size-margin, size-margin], 
            radius=size//8,
            fill=(76, 175, 80, 255)  # Android Material Green
        )
        
        # Add a phone icon representation
        if size >= 64:
            phone_margin = size // 4
            phone_width = size // 8
            draw.rounded_rectangle(
                [phone_margin, phone_margin, size-phone_margin, size-phone_margin],
                radius=size//20,
                outline=(255, 255, 255, 255),
                width=phone_width//4 or 1
            )
            
            # Add "crash" lightning bolt if icon is big enough
            if size >= 128:
                center_x = size // 2
                center_y = size // 2
                bolt_size = size // 6
                
                # Simple lightning bolt shape
                points = [
                    (center_x - bolt_size//4, center_y - bolt_size),
                    (center_x + bolt_size//4, center_y - bolt_size//3),
                    (center_x, center_y),
                    (center_x + bolt_size//4, center_y + bolt_size//3),
                    (center_x - bolt_size//4, center_y + bolt_size)
                ]
                draw.polygon(points, fill=(255, 193, 7, 255))  # Amber warning color
        
        images.append((size, img))
    
    return images

def save_icon_files(images):
    """Save icons in various formats"""
    
    # Create icons directory
    os.makedirs('icons', exist_ok=True)
    
    # Save individual PNG files
    for size, img in images:
        img.save(f'icons/icon_{size}x{size}.png')
    
    # Create .ico file for Windows compatibility
    ico_sizes = [(s, i) for s, i in images if s <= 256]
    if ico_sizes:
        ico_images = [img for _, img in ico_sizes]
        ico_images[0].save('icons/app_icon.ico', format='ICO', 
                          sizes=[(s, s) for s, _ in ico_sizes])
    
    # Create .icns file for macOS
    try:
        # For macOS .icns, we need specific sizes
        icns_sizes = [16, 32, 64, 128, 256, 512, 1024]
        icns_images = []
        
        for target_size in icns_sizes:
            # Find the closest size or create it
            found = False
            for size, img in images:
                if size == target_size:
                    icns_images.append(img)
                    found = True
                    break
            
            if not found and images:
                # Resize the largest available image
                largest = max(images, key=lambda x: x[0])[1]
                resized = largest.resize((target_size, target_size), Image.Resampling.LANCZOS)
                icns_images.append(resized)
        
        if icns_images:
            # Save as ICNS (requires pillow-heif or other plugin for full support)
            # For now, save the largest as PNG and we'll convert manually
            largest_img = max(images, key=lambda x: x[0])[1]
            largest_img.save('icons/app_icon.png')
            print("Saved app_icon.png - use 'sips -s format icns app_icon.png --out app_icon.icns' to convert")
    
    except Exception as e:
        print(f"Note: Could not create .icns file directly: {e}")
        print("Use 'brew install imagemagick' and 'convert app_icon.png app_icon.icns'")

if __name__ == "__main__":
    try:
        print("Creating app icon...")
        images = create_app_icon()
        save_icon_files(images)
        print("App icon created successfully in icons/ directory")
        
    except ImportError:
        print("PIL (Pillow) is required for icon creation.")
        print("Install with: pip install Pillow")
        exit(1)
    except Exception as e:
        print(f"Error creating icon: {e}")
        exit(1)