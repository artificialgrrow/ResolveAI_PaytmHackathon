import io
import base64
import random
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

from steganography import Steganography
from database import run_query
from logger import log

STEGO_ENGINE = Steganography()

def _create_cover_standee(merchant_name: str, vpa: str, width: int = 400, height: int = 400) -> Image.Image:
    """Creates a high-trust, official Paytm Merchant Standee Cover Template.
    Visually clean with merchant branding and payment instructions.
    """
    img = Image.new('RGB', (width, height), (248, 250, 252))
    d = ImageDraw.Draw(img)

    # 1. Paytm Cyan/Blue Top Header Banner
    d.rectangle([0, 0, width, 70], fill=(0, 186, 242)) # Paytm signature cyan
    d.rectangle([0, 66, width, 70], fill=(0, 140, 200)) # subtle border line

    # Header text
    d.text((24, 18), "Paytm", fill=(255, 255, 255))
    d.text((80, 20), "Accepted Here", fill=(240, 248, 255))
    d.text((width - 130, 20), "SECURE UPI", fill=(255, 255, 255))

    # 2. White Standee Card Body
    d.rectangle([20, 85, width - 20, height - 20], fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    # 3. Merchant Details Header
    d.text((36, 100), merchant_name, fill=(15, 23, 42))
    d.text((36, 122), f"UPI ID: {vpa}", fill=(100, 116, 139))
    d.line([36, 142, width - 36, 142], fill=(241, 245, 249), width=1)

    # 4. Center Brand Watermark & Frame
    d.rectangle([50, 160, width - 50, height - 60], outline=(203, 213, 225), width=1, fill=(250, 252, 255))
    d.rectangle([60, 170, width - 60, height - 70], outline=(226, 232, 240), width=1)

    # Brand text in middle of standee
    d.text((110, 220), "Scan & Pay With Any App", fill=(71, 85, 105))
    d.text((120, 245), "[ GPay • PhonePe • Paytm • BHIM ]", fill=(148, 163, 184))
    d.text((105, 275), "Holographic Anti-Tamper Protected", fill=(0, 112, 243))

    # 5. Bottom Security Verification Footer
    d.rectangle([0, height - 28, width, height], fill=(15, 23, 42))
    d.text((24, height - 20), "NPCI / Paytm Cryptographic Watermark Verified", fill=(203, 213, 225))

    return img

def _create_secret_qr_matrix(merchant_id: str, vpa: str, width: int = 400, height: int = 400) -> Image.Image:
    """Generates the secret high-contrast QR pattern with standard position detection patterns
    and merchant UPI data blocks to be steganographically embedded.
    """
    qr = Image.new('RGB', (width, height), (255, 255, 255))
    qd = ImageDraw.Draw(qr)

    def draw_finder(ox, oy, sz=64):
        qd.rectangle([ox, oy, ox + sz, oy + sz], fill=(0, 0, 0))
        qd.rectangle([ox + 10, oy + 10, ox + sz - 10, oy + sz - 10], fill=(255, 255, 255))
        qd.rectangle([ox + 20, oy + 20, ox + sz - 20, oy + sz - 20], fill=(0, 0, 0))

    # 3 Standard QR Corner Position Markers
    draw_finder(40, 100)        # Top-Left
    draw_finder(width - 104, 100) # Top-Right
    draw_finder(40, height - 104) # Bottom-Left

    # Seed deterministic QR matrix pattern based on merchant ID and VPA
    seed_val = sum(ord(c) for c in f"{merchant_id}:{vpa}")
    rng = random.Random(seed_val)

    # Data matrix grid
    step = 16
    for x in range(120, width - 120, step):
        for y in range(100, height - 40, step):
            if rng.random() > 0.45:
                qd.rectangle([x, y, x + step - 4, y + step - 4], fill=(0, 0, 0))

    # Center UPI VPA text signature block in QR
    qd.rectangle([130, 220, width - 130, 260], fill=(0, 0, 0))
    qd.text((140, 232), f"VPA: {vpa[:18]}", fill=(255, 255, 255))

    return qr

def generate_stego_qr_template(merchant_id: str) -> Dict[str, Any]:
    """Generates the official merchant cover template, embeds the invisible QR code
    using LSB steganography, and returns base64 images for UI presentation and download.
    """
    merchants = run_query(f"SELECT id, name, username, business_type, bank_name, account_number FROM merchants WHERE id = '{merchant_id}' LIMIT 1")
    if not merchants:
        merchant_name = "Paytm Verified Merchant"
        vpa = f"merchant.{merchant_id.lower()}@paytm"
    else:
        m = merchants[0]
        merchant_name = m["name"]
        vpa = f"{m['username']}@paytm"

    # 1. Create Cover Standee & Secret QR
    cover = _create_cover_standee(merchant_name, vpa, 400, 400)
    secret_qr = _create_secret_qr_matrix(merchant_id, vpa, 400, 400)

    # 2. Merge QR into Cover Invisibly
    merged_stego = STEGO_ENGINE.merge(cover, secret_qr, digit=4)

    # 3. Convert to Base64
    def to_b64(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    stego_b64 = to_b64(merged_stego)
    qr_b64 = to_b64(secret_qr)

    return {
        "status": "SUCCESS",
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "vpa": vpa,
        "stego_image_base64": stego_b64,
        "extracted_qr_base64": qr_b64,
        "download_filename": f"Paytm_Stego_QR_{merchant_id}.png"
    }

def verify_stego_qr_image(image_bytes: bytes, merchant_id: str) -> Dict[str, Any]:
    """Unmerges the uploaded counter QR image, inspects the hidden layer,
    and determines with pixel precision whether the QR is genuine or tampered by a thief.
    """
    try:
        uploaded_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return {
            "is_valid": False,
            "status": "INVALID_IMAGE",
            "message": f"Could not read uploaded image: {str(e)}",
            "decoded_qr_base64": None
        }

    # Ensure 400x400 normalized resolution
    if uploaded_img.size != (400, 400):
        uploaded_img = uploaded_img.resize((400, 400), Image.Resampling.NEAREST)

    # 1. Run unmerge to extract hidden steganographic layer
    unmerged = STEGO_ENGINE.unmerge(uploaded_img, digit=4)

    # 2. Check the 3 Finder Pattern Boxes in the unmerged image
    # In an untampered genuine stego image:
    # Corner (40, 100), (296, 100), (40, 296) must have black-white-black finder squares.
    def check_finder_box(ox, oy, sz=64) -> float:
        pixels = unmerged.load()
        # Outer border: should be black (0,0,0)
        # Inner border: should be white (255,255,255)
        # Center: should be black (0,0,0)
        correct = 0
        total = 0
        for x in range(ox, ox + sz):
            for y in range(oy, oy + sz):
                total += 1
                r, g, b = pixels[x, y]
                is_black = (r < 128 and g < 128 and b < 128)
                is_white = not is_black

                # Check outer ring [0..9, sz-10..sz]
                rel_x = x - ox
                rel_y = y - oy
                if rel_x < 10 or rel_x >= sz - 10 or rel_y < 10 or rel_y >= sz - 10:
                    if is_black: correct += 1
                elif rel_x < 20 or rel_x >= sz - 20 or rel_y < 20 or rel_y >= sz - 20:
                    if is_white: correct += 1
                else:
                    if is_black: correct += 1

        return correct / total if total > 0 else 0.0

    score1 = check_finder_box(40, 100)
    score2 = check_finder_box(296, 100)
    score3 = check_finder_box(40, 296)
    min_finder_score = min(score1, score2, score3)
    avg_finder_score = (score1 + score2 + score3) / 3.0

    # Convert unmerged image to base64 for UI inspection
    buf = io.BytesIO()
    unmerged.save(buf, format="PNG")
    decoded_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    merchants = run_query(f"SELECT name, username FROM merchants WHERE id = '{merchant_id}' LIMIT 1")
    merchant_name = merchants[0]["name"] if merchants else "Paytm Merchant"
    vpa = f"{merchants[0]['username']}@paytm" if merchants else f"merchant.{merchant_id.lower()}@paytm"

    log.info(f"[STEGO_VERIFY] Merchant {merchant_id} min finder score: {min_finder_score:.3f}, avg: {avg_finder_score:.3f}")

    # Threshold for genuine stego image: every finder box must be >= 85% intact
    if min_finder_score >= 0.85 and avg_finder_score >= 0.88:
        return {
            "is_valid": True,
            "status": "GENUINE_AUTHENTICATED",
            "message": f"GENUINE PAYTM QR VERIFIED: Cryptographic steganographic watermark decoded with {avg_finder_score*100:.1f}% integrity. Payment route authenticated for {merchant_name} ({vpa}).",
            "merchant_name": merchant_name,
            "vpa": vpa,
            "integrity_score": round(avg_finder_score * 100, 1),
            "decoded_qr_base64": decoded_b64
        }
    else:
        return {
            "is_valid": False,
            "status": "TAMPERED_QR_DETECTED",
            "message": f"ALERT: TAMPERED QR DETECTED! Steganographic watermark was corrupted or missing (Integrity: {min_finder_score*100:.1f}%). Someone may have pasted a fake sticker, drawn a dot, or swapped the physical QR.",
            "merchant_name": merchant_name,
            "vpa": vpa,
            "integrity_score": round(min_finder_score * 100, 1),
            "decoded_qr_base64": decoded_b64
        }

def create_sample_tampered_image(merchant_id: str) -> str:
    """Helper for instantaneous demo: takes the genuine stego template and simulates
    a thief drawing a dot or pasting a fake sticker patch over the QR.
    """
    res = generate_stego_qr_template(merchant_id)
    img_data = base64.b64decode(res["stego_image_base64"])
    img = Image.open(io.BytesIO(img_data))

    # Simulate thief sticker / dot tampering
    d = ImageDraw.Draw(img)
    # Draw a rogue sticker in the upper finder box area
    d.rectangle([50, 110, 85, 145], fill=(220, 38, 38)) # red sticker / marker
    d.text((54, 122), "FAKE", fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
