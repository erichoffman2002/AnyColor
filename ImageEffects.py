import numpy as np
from PIL import Image, ImageFilter, ImageChops
import colorsys
import math

def adjust_pixel(r, g, b, a, cr_offset, mg_offset, yb_offset, hue_offset):
    """Adjust a single pixel's color values"""
    # Convert input to numpy arrays for faster processing
    rgb = np.array([r, g, b]) / 255.0
    
    # Only process if pixel is not transparent
    if a == 0:
        return r, g, b, a
        
    # Convert to HSV
    max_val = rgb.max()
    min_val = rgb.min()
    diff = max_val - min_val
    
    # Calculate Hue
    h = 0
    if diff != 0:
        if max_val == rgb[0]:  # r is max
            h = (rgb[1] - rgb[2]) / diff % 6
        elif max_val == rgb[1]:  # g is max
            h = (rgb[2] - rgb[0]) / diff + 2
        else:  # b is max
            h = (rgb[0] - rgb[1]) / diff + 4
    h = (h / 6 + hue_offset) % 1.0
    
    # Calculate Saturation and Value
    s = np.divide(diff, max_val, out=np.zeros_like(diff), where=max_val!=0)
    v = max_val
    
    # Convert back to RGB
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    
    if h < 1/6:
        rgb = np.array([c, x, 0])
    elif h < 2/6:
        rgb = np.array([x, c, 0])
    elif h < 3/6:
        rgb = np.array([0, c, x])
    elif h < 4/6:
        rgb = np.array([0, x, c])
    elif h < 5/6:
        rgb = np.array([x, 0, c])
    else:
        rgb = np.array([c, 0, x])
        
    # Add back the m value and apply color offsets
    rgb = (rgb + m) * 255
    rgb[0] = max(0, min(255, int(rgb[0] + cr_offset * 255)))
    rgb[1] = max(0, min(255, int(rgb[1] + mg_offset * 255)))
    rgb[2] = max(0, min(255, int(rgb[2] + yb_offset * 255)))
    
    return int(rgb[0]), int(rgb[1]), int(rgb[2]), a

def apply_color_option(option, image):
    """Applies color effects to the image using NumPy vectorization"""
    # Convert image to NumPy array
    img_array = np.array(image)
    alpha = img_array[:, :, 3]
    mask = alpha > 0
    
    if not mask.any():  # No non-transparent pixels to process
        return image
        
    if option == "Greyscale":
        # Use luminosity method with NumPy broadcasting
        rgb = img_array[mask, :3].astype(np.float32)
        grey = np.dot(rgb, [0.299, 0.587, 0.114]).astype(np.uint8)
        img_array[mask, 0] = grey
        img_array[mask, 1] = grey
        img_array[mask, 2] = grey
        return Image.fromarray(img_array)
    
    # Convert RGB to HSV using NumPy operations
    rgb = img_array[mask, :3].astype(np.float32) / 255.0
    max_val = np.max(rgb, axis=1)
    min_val = np.min(rgb, axis=1)
    diff = max_val - min_val
    
    # Calculate Hue
    h = np.zeros_like(max_val)
    diff_mask = diff != 0
    
    # Red is maximum
    idx = (rgb[:, 0] == max_val) & diff_mask
    h[idx] = (rgb[idx, 1] - rgb[idx, 2]) / diff[idx] % 6
    
    # Green is maximum
    idx = (rgb[:, 1] == max_val) & diff_mask
    h[idx] = (rgb[idx, 2] - rgb[idx, 0]) / diff[idx] + 2
    
    # Blue is maximum
    idx = (rgb[:, 2] == max_val) & diff_mask
    h[idx] = (rgb[idx, 0] - rgb[idx, 1]) / diff[idx] + 4
    
    h = h / 6.0  # Convert to [0,1] range
    
    # Calculate Saturation and Value
    s = np.divide(diff, max_val, out=np.zeros_like(diff), where=max_val!=0)
    v = max_val
    
    # Apply effects using vectorized operations
    if option == "Neon Outburst":
        s = np.minimum(1.0, s * 1.8)
        v = np.minimum(1.0, v * 1.2)
    elif option == "Cyber Glow":
        h = (h + 0.1) % 1.0
        v = np.minimum(1.0, v * 1.3)
    elif option == "Aurora Prism":
        x_coords = np.tile(np.arange(image.width), (image.height, 1))[mask]
        h = (h + (x_coords / image.width) * 0.2) % 1.0
        s = np.minimum(1.0, s * 1.2)
    elif option == "Chromatic Fragment":
        s *= 0.8
        h = (h + 0.05) % 1.0
    elif option == "Vibrant Spectrum":
        s = np.minimum(1.0, s * 1.5)
    elif option == "Mystic Mirage":
        s *= 0.7
        v = np.minimum(1.0, v * 1.4)
    elif option == "Holographic Shift":
        y_coords = np.repeat(np.arange(image.height)[:, np.newaxis], image.width, axis=1)[mask]
        h = (h + (y_coords / image.height) * 0.3) % 1.0
    elif option == "Quantum Leap":
        # Direct RGB inversion
        img_array[mask, :3] = 255 - img_array[mask, :3]
        return Image.fromarray(img_array)
    elif option == "Psychedelic Cascade":
        x_coords = np.tile(np.arange(image.width), (image.height, 1))[mask]
        y_coords = np.repeat(np.arange(image.height)[:, np.newaxis], image.width, axis=1)[mask]
        h = (h + ((x_coords + y_coords) / (image.width + image.height)) * 0.5) % 1.0
    elif option == "Digital Overdrive":
        v = 0.5 + (v - 0.5) * 1.8
        v = np.clip(v, 0, 1)
    elif option == "Earth Tones":
        h = (h + 0.05) % 1.0
        s *= 0.6
        v *= 0.95
    elif option == "Pastel Palette":
        s *= 0.5
        v = v + (1.0 - v) * 0.3
    
    # Convert back to RGB
    c = v * s
    h_prime = h * 6.0
    x = c * (1 - np.abs(h_prime % 2 - 1))
    m = v - c
    
    # Initialize output RGB array
    rgb_out = np.zeros_like(rgb)
    
    # Apply RGB conversion based on hue
    idx = (h_prime < 1)
    rgb_out[idx] = np.column_stack((c[idx], x[idx], np.zeros_like(x[idx])))
    
    idx = (h_prime >= 1) & (h_prime < 2)
    rgb_out[idx] = np.column_stack((x[idx], c[idx], np.zeros_like(x[idx])))
    
    idx = (h_prime >= 2) & (h_prime < 3)
    rgb_out[idx] = np.column_stack((np.zeros_like(x[idx]), c[idx], x[idx]))
    
    idx = (h_prime >= 3) & (h_prime < 4)
    rgb_out[idx] = np.column_stack((np.zeros_like(x[idx]), x[idx], c[idx]))
    
    idx = (h_prime >= 4) & (h_prime < 5)
    rgb_out[idx] = np.column_stack((x[idx], np.zeros_like(x[idx]), c[idx]))
    
    idx = (h_prime >= 5)
    rgb_out[idx] = np.column_stack((c[idx], np.zeros_like(x[idx]), x[idx]))
    
    # Add back the value offset and convert to 8-bit
    rgb_out = np.clip((rgb_out + m[:, np.newaxis]) * 255, 0, 255).astype(np.uint8)
    
    # Update the image array
    img_array[mask, :3] = rgb_out
    
    return Image.fromarray(img_array)

def apply_glow_effect(effect_type, image, start_color_slider, border_width_slider):
    """Applies a colored glow or border effect"""
    if effect_type == "None":
        return image
        
    # Get color directly from the slider - no hue adjustment
    hue = start_color_slider.value() / 360.0
    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
    
    # Get the width from slider
    glow_width = border_width_slider.value()
    
    # Convert image to numpy array for faster processing
    img_array = np.array(image)
    
    # Create mask from alpha channel
    alpha_mask = (img_array[:, :, 3] > 0).astype(np.uint8) * 255
    letter_mask = Image.fromarray(alpha_mask)

    if effect_type == "glow":  # Glow effect
        # Apply gaussian blur to mask
        test_layer = letter_mask.filter(ImageFilter.GaussianBlur(glow_width * 2))
        blur_array = np.array(test_layer)
        
        # Create glow layer using numpy operations
        mask_3d = blur_array[:, :, np.newaxis]
        glow_layer = np.zeros_like(img_array)
        glow_layer[:, :, 0] = r
        glow_layer[:, :, 1] = g
        glow_layer[:, :, 2] = b
        glow_layer[:, :, 3] = np.where(img_array[:, :, 3] == 0, blur_array, 0)
        
        # Convert back to PIL for alpha compositing
        glow_image = Image.fromarray(glow_layer, 'RGBA')
        
        # Composite the glow under the original image
        result = Image.alpha_composite(glow_image, image)
        image.paste(result, (0, 0))

    elif effect_type == "border":  # Border effect
        # Use MaxFilter for dilation
        filter_size = glow_width * 2 + 1
        dilated_mask = letter_mask.filter(ImageFilter.MaxFilter(filter_size))
        dilated_array = np.array(dilated_mask)
        
        # Create border mask using numpy operations
        border_mask = dilated_array - alpha_mask
        
        # Create border layer
        border_layer = np.zeros_like(img_array)
        border_layer[:, :, 0] = r
        border_layer[:, :, 1] = g
        border_layer[:, :, 2] = b
        border_layer[:, :, 3] = border_mask
        
        # Convert back to PIL for compositing
        border_image = Image.fromarray(border_layer, 'RGBA')
        
        # Composite border with original image
        result = Image.alpha_composite(border_image, image)
        image.paste(result, (0, 0))

    return image

def save_image_with_transparency(image, file_path, transparency):
    """Save image with or without transparency based on checkbox state"""
    if transparency:
        # Save with transparency (RGBA)
        image.save(file_path, 'PNG')
    else:
        # Save with white background (RGB)
        background = Image.new("RGB", image.size, (255, 255, 255))
        # Use alpha composite to properly blend with white background
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3])
        else:
            background.paste(image)
        background.save(file_path, 'PNG')

def get_gradient_colors(x, y, width, height, start_hue, end_hue, gradient_type, gradient_direction):
    """Calculate color based on position and current settings"""
    if gradient_type == "Linear":
        if gradient_direction == "Horizontal":
            t = x / width
        elif gradient_direction == "Vertical":
            t = y / height
        elif gradient_direction == "Diagonal ↘":
            t = (x + y) / (width + height)
        else:  # "Diagonal ↗"
            t = (x + (height - y)) / (width + height)
    elif gradient_type == "Radial":
        center_x, center_y = width / 2, height / 2
        distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
        max_distance = ((width / 2) ** 2 + (height / 2) ** 2) ** 0.5
        t = min(distance / max_distance, 1.0)
    else:  # "Angular"
        center_x, center_y = width / 2, height / 2
        angle = math.atan2(y - center_y, x - center_x)
        t = (angle + math.pi) / (2 * math.pi)
        
    hue = start_hue + t * ((end_hue - start_hue) % 1.0)
    return [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]

def adjust_image_size(image, effect_type, border_width):
    """Adjust image size based on border/glow width"""
    if not image or effect_type == "None":
        return image
        
    # Increase padding multiplier to account for full glow spread
    if effect_type == "glow":
        padding = border_width * 8  # Double the padding for glow effects
    else:
        padding = border_width * 4  # Original padding for border effects
    
    # Create new image with padding
    new_width = image.width + padding
    new_height = image.height + padding
    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    
    # Paste original image in center
    paste_x = padding // 2
    paste_y = padding // 2
    new_image.paste(image, (paste_x, paste_y))
    
    return new_image

def adjust_size_for_glow(image, effect_type, border_width):
    """Adjust image size for glow using the current adjusted image"""
    if not image:
        return image
        
    # Increase padding multiplier based on effect type
    if effect_type == "glow":
        padding = border_width * 8  # For glow effects
    else:
        padding = border_width * 4  # For border effects
        
    new_width = image.width + padding
    new_height = image.height + padding
    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    paste_x = padding // 2
    paste_y = padding // 2
    new_image.paste(image, (paste_x, paste_y))
    
    return new_image 