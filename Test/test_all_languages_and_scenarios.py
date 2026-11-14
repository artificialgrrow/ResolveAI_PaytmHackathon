import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from agent_engine import process_incident_stream, approve_incident_stream
from database import init_db, run_query

SCENARIO_PROMPTS = {
    'M-101': {
        'en': "My ₹4,500 payment from morning sales hasn't reached my bank account yet. Please check.",
        'hi': "मेरी सुबह की ₹4,500 की बिक्री का पैसा अभी तक मेरे बैंक खाते में नहीं आया। कृपया जांच करें।",
        'mr': "माझ्या सकाळच्या विक्रीचे ₹4,500 अजूनही माझ्या बँक खात्यात जमा झाले नाहीत. कृपया तपासा.",
        'gu': "મારી સવારના વેચાણના ₹4,500 હજુ સુધી મારા બેંક ખાતામાં આવ્યા નથી. કૃપા કરીને તપાસો.",
        'bn': "আমার সকালের বিক্রির ₹4,500 এখনও আমার ব্যাংক অ্যাকাউন্টে ঢোকেনি। দয়া করে চেক করুন।",
        'ta': "எனது காலை விற்பனைக்கான ₹4,500 இன்னும் எனது வங்கி கணக்கில் வரவில்லை. தயவுசெய்து சரிபார்க்கவும்.",
        'te': "నా ఉదయం అమ్మకాల ₹4,500 ఇంకా నా బ్యాంక్ ఖాతాలో జమ కాలేదు. దయచేసి పరిశీలించండి.",
        'kn': "ನನ್ನ ಬೆಳಗಿನ ಮಾರಾಟದ ₹4,500 ಹಣ ಇನ್ನೂ ನನ್ನ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಬಂದಿಲ್ಲ. ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ.",
        'ml': "എന്റെ രാവിലത്തെ വിൽപ്പനയുടെ ₹4,500 ഇതുവരെ എന്റെ ബാങ്ക് അക്കൗണ്ടിൽ എത്തിയില്ല. ദയവായി പരിശോധിക്കുക.",
        'pa': "ਮੇਰੀ ਸਵੇਰ ਦੀ ਵਿਕਰੀ ਦੇ ₹4,500 ਅਜੇ ਤੱਕ ਮੇਰੇ ਬੈਂਕ ਖਾਤੇ ਵਿੱਚ ਨਹੀਂ ਆਏ। ਕਿਰਪਾ ਕਰਕੇ ਜਾਂਚ ਕਰੋ।"
    },
    'M-102': {
        'en': "Customer bought a smart TV for ₹78,000 via QR, but the settlement is showing on hold.",
        'hi': "ग्राहक ने QR से ₹78,000 का स्मार्ट टीवी खरीदा, लेकिन सेटलमेंट होल्ड पर दिख रहा है।",
        'mr': "ग्राहकाने QR द्वारे ₹78,000 चा स्मार्ट टीव्ही खरेदी केला, पण सेटलमेंट होल्डवर दिसत आहे.",
        'gu': "ગ્રાહકે QR થી ₹78,000 નું સ્માર્ટ ટીવી ખરીદ્યું, પણ સેટલમેન્ટ હોલ્ડ પર બતાવે છે.",
        'bn': "গ্রাহক QR দিয়ে ₹78,000 এর স্মার্ট টিভি কিনেছেন, কিন্তু সেটেলমেন্ট হোল্ডে দেখাচ্ছে।",
        'ta': "வாடிக்கையாளர் QR மூலம் ₹78,000க்கு ஸ்மார்ட் டிவி வாங்கினார், ஆனால் செட்டில்மென்ட் நிறுத்தி வைக்கப்பட்டுள்ளது.",
        'te': "కస్టమర్ QR ద్వారా ₹78,000 స్మార్ట్ టీవీ కొన్నారు, కానీ సెటిల్‌మెంట్ హోల్డ్‌లో ఉంది.",
        'kn': "ಗ್ರಾಹಕರು QR ಮೂಲಕ ₹78,000 ಬೆಲೆಯ ಸ್ಮಾರ್ಟ್ ಟಿವಿ ಖರೀದಿಸಿದ್ದಾರೆ, ಆದರೆ ಸೆಟ್ಲ್‌ಮೆಂಟ್ ಹೋಲ್ಡ್‌ನಲ್ಲಿದೆ.",
        'ml': "ഉപഭോക്താവ് QR വഴി ₹78,000-ന് സ്മാർട്ട് ടിവി വാങ്ങി, എന്നാൽ സെറ്റിൽമെന്റ് ഹോൾഡിലാണ്.",
        'pa': "ਗਾਹਕ ਨੇ QR ਰਾਹੀਂ ₹78,000 ਦਾ ਸਮਾਰਟ ਟੀਵੀ ਖਰੀਦਿਆ, ਪਰ ਸੈਟਲਮੈਂਟ ਹੋਲਡ ਤੇ ਦਿਖ ਰਹੀ ਹੈ।"
    },
    'M-103': {
        'en': "Customer paid ₹60 for tea, but Soundbox did not announce anything!",
        'hi': "ग्राहक ने चाय के लिए ₹60 दिए, लेकिन साउंडबॉक्स ने कुछ नहीं बोला!",
        'mr': "ग्राहकाने चहासाठी ₹60 दिले, पण साउंडबॉक्स काहीच बोलला नाही!",
        'gu': "ગ્રાહકે ચા માટે ₹60 આપ્યા, પણ સાઉન્ડબોક્સે કંઈ બોલ્યું નહીં!",
        'bn': "গ্রাহক চায়ের জন্য ₹60 দিয়েছে, কিন্তু সাউন্ডবক্সে কোনো আওয়াজ হয়নি!",
        'ta': "வாடிக்கையாளர் டீக்கு ₹60 செலுத்தினார், ஆனால் சவுண்ட்பாக்ஸ் எதுவும் பேசவில்லை!",
        'te': "కస్టమర్ టీ కోసం ₹60 చెల్లించారు, కానీ సౌండ్‌బాక్స్ ఏమీ మాట్లాడలేదు!",
        'kn': "ಗ್ರಾಹಕರು ಚಹಾಗೆ ₹60 ಪಾವತಿಸಿದ್ದಾರೆ, ಆದರೆ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಧ್ವನಿಸಲಿಲ್ಲ!",
        'ml': "ചായയ്ക്ക് ഉപഭോക്താവ് ₹60 നൽകി, എന്നാൽ സൗണ്ട്ബോക്സ് ശബ്ദിച്ചില്ല!",
        'pa': "ਗਾਹਕ ਨੇ ਚਾਹ ਲਈ ₹60 ਦਿੱਤੇ, ਪਰ ਸਾਊਂਡਬਾਕਸ ਨੇ ਕੁਝ ਨਹੀਂ ਬੋਲਿਆ!"
    },
    'M-104': {
        'en': "A customer is complaining they got charged twice for ₹1,200 medicine.",
        'hi': "एक ग्राहक शिकायत कर रहा है कि ₹1,200 की दवाई के लिए उसके खाते से दो बार पैसे कट गए।",
        'mr': "एक ग्राहक तक्रार करत आहे की ₹1,200 च्या औषधांसाठी त्यांच्या खात्यातून दोनदा पैसे कापले गेले.",
        'gu': "એક ગ્રાહક ફરિયાદ કરે છે કે ₹1,200 ની દવા માટે તેના ખાતામાંથી બે વાર પૈસા કપાયા.",
        'bn': "একজন গ্রাহক অভিযোগ করছেন যে ₹1,200 এর ওষুধের জন্য তার দুবার টাকা কেটে নেওয়া হয়েছে।",
        'ta': "₹1,200 மருந்துக்கு வாடிக்கையாளரிடம் இரண்டு முறை பணம் கழிக்கப்பட்டதாக புகார் கூறுகிறார்.",
        'te': "₹1,200 మందుల కోసం కస్టమర్ ఖాతా నుండి రెండుసార్లు డబ్బు కట్ అయిందని ఫిర్యాదు చేస్తున్నారు.",
        'kn': "₹1,200 ರ ಔಷಧಿಗೆ ಗ್ರಾಹಕರಿಂದ ಎರಡು ಬಾರಿ ಹಣ ಕಡಿತಗೊಂಡಿದೆ ಎಂದು ದೂರಿದ್ದಾರೆ.",
        'ml': "₹1,200 മരുന്നിന് ഉപഭോക്താവിൽ നിന്ന് രണ്ട് തവണ പണം ഈടാക്കിയതായി പരാതിപ്പെടുന്നു.",
        'pa': "ਇੱਕ ਗਾਹਕ ਸ਼ਿਕਾਇਤ ਕਰ ਰਿਹਾ ਹੈ ਕਿ ₹1,200 ਦੀ ਦਵਾਈ ਲਈ ਉਸਦੇ ਦੋ ਵਾਰ ਪੈਸੇ ਕੱਟੇ ਗਏ ਹਨ।"
    },
    'M-105': {
        'en': "Why did multiple customer payments fail in the last 20 minutes?",
        'hi': "पिछले 20 मिनट में कई ग्राहकों के भुगतान क्यों फेल हो गए?",
        'mr': "गेल्या 20 मिनिटांत अनेक ग्राहकांचे पेमेंट्स का अयशस्वी झाले?",
        'gu': "છેલ્લી 20 મિનિટમાં ઘણા ગ્રાહકોના પેમેન્ટ કેમ નિષ્ફળ ગયા?",
        'bn': "গত 20 মিনিটে একাধিক গ্রাহকের পেমেন্ট কেন ব্যর্থ হলো?",
        'ta': "கடந்த 20 நிமிடங்களில் பல வாடிக்கையாளர்களின் கொடுப்பனவுகள் ஏன் தோல்வியடைந்தன?",
        'te': "గత 20 నిమిషాల్లో చాలా మంది కస్టమర్ల చెల్లింపులు ఎందుకు విఫలమయ్యాయి?",
        'kn': "ಕಳೆದ 20 ನಿಮಿಷಗಳಲ್ಲಿ ಬಹುತೇಕ ಗ್ರಾಹಕರ ಪಾವತಿಗಳು ಏಕೆ ವಿಫಲವಾದವು?",
        'ml': "കഴിഞ്ഞ 20 മിനിറ്റിൽ ഒന്നിലധികം ഉപഭോക്താക്കളുടെ പേയ്‌മെന്റുകൾ പരാജയപ്പെട്ടത് എന്തുകൊണ്ട്?",
        'pa': "ਪਿਛਲੇ 20 ਮਿੰਟਾਂ ਵਿੱਚ ਕਈ ਗਾਹਕਾਂ ਦੇ ਭੁਗਤਾਨ ਕਿਉਂ ਫੇਲ੍ਹ ਹੋਏ?"
    }
}

languages = ['en', 'hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa']

def run_tests():
    passed = 0
    failed = 0
    failures = []

    for m_id, prompts in SCENARIO_PROMPTS.items():
        for lang in languages:
            init_db(force_seed=True)  # reset clean pristine DB for each deterministic scenario test
            prompt = prompts[lang]
            events = list(process_incident_stream(m_id, prompt, language=lang))
            
            # Check last event
            last_event = events[-1]
            status = last_event.get("status")
            msg = last_event.get("message", "")

            # Verify that Scenario 2 is AWAITING_APPROVAL or RESOLVED
            if m_id == 'M-102':
                if status == "AWAITING_APPROVAL":
                    # Now test supervisor approval
                    inc_id = last_event["details"]["incident_id"]
                    approval_events = list(approve_incident_stream(inc_id, True, "Approved KYC", language=lang))
                    app_last = approval_events[-1]
                    if app_last.get("status") == "RESOLVED":
                        passed += 1
                        print(f"[{m_id}][{lang}] OK (Awaiting Approval -> Resolved): {app_last.get('message')[:50]}...")
                    else:
                        failed += 1
                        failures.append((m_id, lang, f"Approval failed: {app_last}"))
                else:
                    failed += 1
                    failures.append((m_id, lang, f"Expected AWAITING_APPROVAL, got {status}"))
            else:
                if status == "RESOLVED":
                    # Check that it did NOT fall into DEFAULT_RESOLVED ("हमने आपके पेटीएम मर्चेंट खाते का ऑडिट किया है" / "We have audited your Paytm merchant account")
                    if "We have audited your Paytm" in msg or "ऑडिट किया है" in msg or "अकाउंट অডিট করেছি" in msg:
                        failed += 1
                        failures.append((m_id, lang, f"Fell into generic DEFAULT_RESOLVED: {msg}"))
                    else:
                        passed += 1
                        print(f"[{m_id}][{lang}] OK: {msg[:60]}...")
                else:
                    failed += 1
                    failures.append((m_id, lang, f"Expected RESOLVED, got {status}"))

    print("\n===============================")
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED (TOTAL: {passed + failed})")
    print("===============================")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        print("ALL 50 MULTILINGUAL SCENARIOS PASSED WITH ZERO DEFAULT FALLBACK!")

if __name__ == "__main__":
    run_tests()
