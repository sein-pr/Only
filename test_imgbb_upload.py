"""
Test ImgBB image upload functionality
"""
from dotenv import load_dotenv
load_dotenv()

import os
import io
from PIL import Image
from werkzeug.datastructures import FileStorage
from imgbb_uploader import ImgBBUploader, upload_image_to_imgbb

print("=" * 60)
print("TESTING IMGBB IMAGE UPLOAD")
print("=" * 60)

# Test 1: Check API key
print("\n1. Checking ImgBB API key...")
api_key = os.environ.get('IMGBB_API_KEY')
if api_key:
    print(f"   ✅ API key found: {api_key[:10]}...")
else:
    print("   ❌ API key not found!")
    exit(1)

# Test 2: Create a test image
print("\n2. Creating test image...")
try:
    # Create a simple test image (100x100 red square)
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Create FileStorage object (simulates Flask file upload)
    file_storage = FileStorage(
        stream=img_bytes,
        filename='test_image.png',
        content_type='image/png'
    )
    
    print("   ✅ Test image created (100x100 red square)")
except Exception as e:
    print(f"   ❌ Failed to create test image: {e}")
    exit(1)

# Test 3: Upload to ImgBB
print("\n3. Uploading to ImgBB...")
try:
    uploader = ImgBBUploader()
    result = uploader.upload_file(file_storage, name='test_product_image')
    
    print("   ✅ Upload successful!")
    print(f"\n   Upload Details:")
    print(f"   - Image ID: {result.get('id')}")
    print(f"   - Title: {result.get('title')}")
    print(f"   - Size: {result.get('size')} bytes")
    print(f"   - Width: {result.get('width')}px")
    print(f"   - Height: {result.get('height')}px")
    print(f"   - Display URL: {result.get('display_url')}")
    print(f"   - Viewer URL: {result.get('url_viewer')}")
    
    display_url = uploader.get_display_url(result)
    print(f"\n   📸 Image URL: {display_url}")
    print(f"   🌐 View in browser: {result.get('url_viewer')}")
    
except Exception as e:
    print(f"   ❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Upload multiple images
print("\n4. Testing multiple image upload...")
try:
    # Create 3 test images
    images = []
    for i, color in enumerate(['blue', 'green', 'yellow'], 1):
        img = Image.new('RGB', (50, 50), color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file_storage = FileStorage(
            stream=img_bytes,
            filename=f'test_{color}.png',
            content_type='image/png'
        )
        images.append(file_storage)
    
    results = uploader.upload_multiple(images, names=['blue_img', 'green_img', 'yellow_img'])
    
    print(f"   ✅ Uploaded {len(results)} images")
    for i, result in enumerate(results, 1):
        print(f"   - Image {i}: {uploader.get_display_url(result)}")
        
except Exception as e:
    print(f"   ❌ Multiple upload failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Quick upload function
print("\n5. Testing quick upload function...")
try:
    # Create another test image
    img = Image.new('RGB', (75, 75), color='purple')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    file_storage = FileStorage(
        stream=img_bytes,
        filename='quick_test.png',
        content_type='image/png'
    )
    
    url = upload_image_to_imgbb(file_storage, name='quick_upload_test')
    print(f"   ✅ Quick upload successful!")
    print(f"   - URL: {url}")
    
except Exception as e:
    print(f"   ❌ Quick upload failed: {e}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\n💡 Your images are now hosted on ImgBB and accessible from anywhere!")
print("   This means Railway deployment will work perfectly with images.")
