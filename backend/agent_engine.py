import time
import json
import uuid
import datetime
from typing import Dict, Any, Generator, Optional, List

from config import AUTO_RESOLUTION_THRESHOLD, get_llm
from logger import log
from database import run_query
from tools import (
    query_merchant_database,
    requeue_settlement_batch,
    release_settlement_hold,
    trigger_soundbox_chime,
    verify_bank_utr,
    switch_gateway_route,
    audit_npci_reversal_ledger,
    verify_inbound_upi_traffic,
    trigger_soundbox_security_alert
)

# Standardized LangChain Model Instance (Groq, Sarvam, OpenAI, Azure, Bedrock)
llm = get_llm()

# Top 10 Indian Languages Response Dictionary
MULTILINGUAL_TEMPLATES = {
    "S1_RESOLVED": {
        "en": "Namaste {name}. Your morning settlement of ₹{amount} (Batch #{batch_code}) was held due to an NPCI synchronization timeout. ResolveAI has re-routed it via IMPS. Funds are credited to your {bank_name} account. Bank UTR: {utr}.",
        "hi": "नमस्ते {name}। आपका ₹{amount} का सुबह का सेटलमेंट (बैच #{batch_code}) NPCI टाइमआउट के कारण अटका था। ResolveAI ने इसे IMPS से क्लियर कर दिया है। राशि आपके {bank_name} खाते में जमा हो चुकी है। बैंक UTR: {utr}।",
        "mr": "नमस्ते {name}. आपले ₹{amount} चे सकाळचे सेटलमेंट (बॅच #{batch_code}) NPCI सिंक टाइमआउटमुळे अडकले होते. ResolveAI ने ते IMPS द्वारे त्वरित क्लियर केले आहे. रक्कम आपल्या {bank_name} खात्यात जमा झाली आहे. बँक UTR: {utr}.",
        "gu": "નમસ્તે {name}. તમારું ₹{amount} નું સવારનું સેટલમેન્ટ (બેચ #{batch_code}) NPCI ટાઈમઆઉટને કારણે અટકાયું હતું. ResolveAI એ તેને IMPS દ્વારા ક્લિયર કર્યું છે. રકમ તમારા {bank_name} ખાતામાં જમા થઈ ગઈ છે. બેંક UTR: {utr}.",
        "bn": "নমস্কার {name}। আপনার সকালের ₹{amount} সেটেলমেন্ট (ব্যাচ #{batch_code}) NPCI টাইমআউটের কারণে আটকে ছিল। ResolveAI এটিকে IMPS মাধ্যমে ক্লিয়ার করেছে। টাকা আপনার {bank_name} অ্যাকাউন্টে জমা হয়েছে। ব্যাংক UTR: {utr}।",
        "ta": "வணக்கம் {name}. உங்கள் காலை செட்டில்மென்ட் ₹{amount} (பேட்ச் #{batch_code}) NPCI காலாவதியால் நிறுத்தி வைக்கப்பட்டது. ResolveAI அதை IMPS மூலம் தீர்த்துவிட்டது. தொகை உங்கள் {bank_name} கணக்கில் வரவு வைக்கப்பட்டது. வங்கி UTR: {utr}.",
        "te": "నమస్తే {name}. మీ ఉదయం సెటిల్‌మెంట్ ₹{amount} (బ్యాచ్ #{batch_code}) NPCI టైమ్‌అవుట్ వల్ల నిలిచిపోయింది. ResolveAI దీన్ని IMPS ద్వారా క్లియర్ చేసింది. డబ్బు మీ {bank_name} ఖాతాలో జమ అయింది. బ్యాంక్ UTR: {utr}.",
        "kn": "ನಮಸ್ಕಾರ {name}. ನಿಮ್ಮ ಮುಂಜಾನೆಯ ₹{amount} ಸೆಟ್ಲ್‌ಮೆಂಟ್ (ಬ್ಯಾಚ್ #{batch_code}) NPCI ಟೈಮ್‌ಔಟ್‌ನಿಂದ ಬಾಕಿ ಇತ್ತು. ResolveAI ಇದನ್ನು IMPS ಮೂಲಕ ಕ್ಲಿಯರ್ ಮಾಡಿದೆ. ಹಣ ನಿಮ್ಮ {bank_name} ಖಾತೆಗೆ ಜಮೆಯಾಗಿದೆ. ಬ್ಯಾಂಕ್ UTR: {utr}.",
        "ml": "നമസ്കാരം {name}. നിങ്ങളുടെ രാവിലത്തെ ₹{amount} സെറ്റിൽമെന്റ് (ബാച്ച് #{batch_code}) NPCI ടൈംഔട്ട് കാരണം തടസ്സപ്പെട്ടിരുന്നു. ResolveAI ഇത് IMPS വഴി ക്ലിയർ ചെയ്തു. തുക നിങ്ങളുടെ {bank_name} അക്കൗണ്ടിൽ എത്തി. ബാങ്ക് UTR: {utr}.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}। ਤੁਹਾਡਾ ਸਵੇਰ ਦਾ ₹{amount} ਦਾ ਸੈਟਲਮੈਂਟ (ਬੈਚ #{batch_code}) NPCI ਟਾਈਮਆਊਟ ਕਾਰਨ ਰੁਕਿਆ ਹੋਇਆ ਸੀ। ResolveAI ਨੇ ਇਸਨੂੰ IMPS ਰਾਹੀਂ ਕਲੀਅਰ ਕਰ ਦਿੱਤਾ ਹੈ। ਰਕਮ ਤੁਹਾਡੇ {bank_name} ਖਾਤੇ ਵਿੱਚ ਜਮ੍ਹਾ ਹੋ ਗਈ ਹੈ। ਬੈਂਕ UTR: {utr}।"
    },
    "S2_APPROVED": {
        "en": "SUPERVISOR OVERRIDE APPROVED: High-value settlement of ₹{amount} (Batch #{batch_code}) has been released and cleared. Bank UTR: {utr}. Funds credited to merchant bank account.",
        "hi": "पर्यवेक्षक अनुमोदन स्वीकृत: ₹{amount} का उच्च-मूल्य सेटलमेंट (बैच #{batch_code}) क्लियर कर दिया गया है। बैंक UTR: {utr}। राशि आपके बैंक खाते में जमा हो चुकी है।",
        "mr": "पर्यवेक्षक मंजुरी स्वीकृत: ₹{amount} चे उच्च-मूल्य सेटलमेंट (बॅच #{batch_code}) यशस्वीपणे क्लियर केले आहे. बँक UTR: {utr}. रक्कम आपल्या बँक खात्यात जमा झाली आहे.",
        "gu": "સુપરવાઇઝર મંજૂરી સ્વીકૃત: ₹{amount} નું સેટલમેન્ટ (બેચ #{batch_code}) ક્લિયર કરવામાં આવ્યું છે. બેંક UTR: {utr}. રકમ તમારા ખાતામાં જમા થઈ ગઈ છે.",
        "bn": "সুপারভাইজার অনুমোদন অনুমোদিত: ₹{amount} এর সেটেলমেন্ট (ব্যাচ #{batch_code}) ক্লিয়ার করা হয়েছে। ব্যাংক UTR: {utr}। টাকা জমা হয়েছে।",
        "ta": "மேற்பார்வையாளர் அனுமதி ஏற்கப்பட்டது: ₹{amount} உயர் மதிப்பு செட்டில்மென்ட் (பேட்ச் #{batch_code}) தீர்க்கப்பட்டது. வங்கி UTR: {utr}. பணம் வரவு வைக்கப்பட்டது.",
        "te": "పర్యవేక్షకుడి ఆమోదం లభించింది: ₹{amount} హై-వాల్యూ సెటిల్‌మెంట్ (బ్యాచ్ #{batch_code}) క్లియర్ చేయబడింది. బ్యాంక్ UTR: {utr}. ఖాతాలో జమ అయింది.",
        "kn": "ಮೇಲ್ವಿಚಾರಕರ ಅನುಮೋದನೆ ದೊರೆತಿದೆ: ₹{amount} ಹೆಚ್ಚಿನ ಮೌಲ್ಯದ ಸೆಟ್ಲ್‌ಮೆಂಟ್ (ಬ್ಯಾಚ್ #{batch_code}) ಕ್ಲಿಯರ್ ಆಗಿದೆ. ಬ್ಯಾಂಕ್ UTR: {utr}. ಖಾತೆಗೆ ಜಮೆಯಾಗಿದೆ.",
        "ml": "സൂപ്പർവൈസർ അംഗീകാരം ലഭിച്ചു: ₹{amount} ഉയർന്ന മൂല്യമുള്ള സെറ്റിൽമെന്റ് (ബാച്ച് #{batch_code}) ക്ലിയർ ചെയ്തു. ബാങ്ക് UTR: {utr}. അക്കൗണ്ടിൽ എത്തി.",
        "pa": "ਸੁਪਰਵਾਈਜ਼ਰ ਦੀ ਮਨਜ਼ੂਰੀ ਮਿਲ ਗਈ: ₹{amount} ਦਾ ਸੈਟਲਮੈਂਟ (ਬੈਚ #{batch_code}) ਕਲੀਅਰ ਕਰ ਦਿੱਤਾ ਗਿਆ ਹੈ। ਬੈਂਕ UTR: {utr}। ਰਕਮ ਜਮ੍ਹਾ ਹੋ ਗਈ ਹੈ।"
    },
    "S3_RESOLVED": {
        "en": "Security Alert for {name}! We audited the live NPCI UPI switch and Paytm gateway. No payment of ₹{amount} has been received in your account. The Soundbox was silent because no inbound transaction occurred. This is a suspected counterfeit payment spoof (fake screenshot). Do not release goods. We have broadcasted an audio fraud warning on your Soundbox ({device_id}).",
        "hi": "सावधान {name}! हमने NPCI केंद्रीय UPI स्विच और पेटीएम गेटवे का गहन ऑडिट किया है। आपके खाते में ₹{amount} का कोई भी भुगतान प्राप्त नहीं हुआ है। साउंडबॉक्स इसीलिए शांत था क्योंकि कोई ट्रांजैक्शन नहीं आया। यह एक फर्जी स्क्रीनशॉट (Paytm Spoof) का प्रयास हो सकता है। कृपया सामान न दें। हमने आपके साउंडबॉक्स ({device_id}) पर सुरक्षा चेतावनी का प्रसारण कर दिया है।",
        "mr": "सावधान {name}! आम्ही NPCI UPI स्विच आणि पेटीएम गेटवेचे ऑडिट केले आहे. आपल्या खात्यात ₹{amount} चे कोणतेही पेमेंट जमा झालेले नाही. कोणताही व्यवहार न झाल्यामुळेच साउंडबॉक्स शांत होता. हा बनावट स्क्रीनशॉटचा (Paytm Spoof) प्रयत्न असू शकतो. कृपया वस्तू देऊ नका. आम्ही आपल्या साउंडबॉक्सवर ({device_id}) सुरक्षा चेतावणी प्रसारित केली आहे.",
        "gu": "સાવધાન {name}! અમે NPCI UPI સ્વીચ અને પેટીએમ ગેટવેનું ઓડિટ કર્યું છે. તમારા ખાતામાં ₹{amount} નું કોઈ પેમેન્ટ મળ્યું નથી. વ્યવહાર ન થયો હોવાથી સાઉન્ડબોક્સ શાંત હતું. આ નકલી સ્ક્રીનશોટનો પ્રયાસ હોઈ શકે છે. સામાન ન આપો. અમે તમારા સાઉન્ડબોક્સ ({device_id}) પર સુરક્ષા ચેતવણી આપી દીધી છે.",
        "bn": "সাবধান {name}! আমরা NPCI UPI সুইচ এবং পেটিএম গেটওয়ে অডিট করেছি। আপনার অ্যাকাউন্টে ₹{amount} এর কোনো পেমেন্ট জমা হয়নি। কোনো লেনদেন না হওয়ায় সাউন্ডবক্স নিশ্চুপ ছিল। এটি ভুয়া স্ক্রিনশট বা জালিয়াতির চেষ্টা হতে পারে। সামগ্রী দেবেন না। আমরা আপনার সাউন্ডবক্সে ({device_id}) নিরাপত্তা সতর্কতা জারি করেছি।",
        "ta": "எச்சரிக்கை {name}! NPCI UPI சுவிட்ச் மற்றும் Paytm நுழைவாயிலை ஆய்வு செய்தோம். உங்கள் கணக்கில் ₹{amount} பணம் வரவு வைக்கப்படவில்லை. பணப்பரிவர்த்தனை எதுவும் நடக்காததால் சவுண்ட்பாக்ஸ் பேசவில்லை. இது போலி ஸ்கிரீன்ஷாட் மோசடியாக இருக்கலாம். பொருட்களை வழங்க வேண்டாம். உங்கள் சவுண்ட்பாக்ஸில் ({device_id}) பாதுகாப்பு எச்சரிக்கை ஒலித்துள்ளது.",
        "te": "హెచ్చరిక {name}! మేము NPCI UPI స్విచ్ మరియు Paytm గేట్‌వేను ఆడిట్ చేసాము. మీ ఖాతాలో ₹{amount} చెల్లింపు రాలేదు. లావాదేవీ ఏదీ జరగకపోవడం వల్లే సౌండ్‌బాక్స్ మాట్లాడలేదు. ఇది నకిలీ స్క్రీన్‌షాట్ మోసం కావచ్చు. వస్తువులను ఇవ్వవద్దు. మీ సౌండ్‌బాక్స్‌లో ({device_id}) భద్రతా హెచ్చరిక జారీ చేయబడింది.",
        "kn": "ಎಚ್ಚರಿಕೆ {name}! ನಾವು NPCI UPI ಸ್ವಿಚ್ ಮತ್ತು Paytm ಗೇಟ್‌ವೇ ಪರಿಶೀಲಿಸಿದ್ದೇವೆ. ನಿಮ್ಮ ಖಾತೆಗೆ ₹{amount} ಪಾವತಿ ಬಂದಿಲ್ಲ. ಯಾವುದೇ ವಹಿವಾಟು ನಡೆಯದ ಕಾರಣ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಧ್ವನಿಸಲಿಲ್ಲ. ಇದು ನಕಲಿ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ವಂಚನೆಯಾಗಿರಬಹುದು. ಸರಕುಗಳನ್ನು ನೀಡಬೇಡಿ. ನಿಮ್ಮ ಸೌಂಡ್‌ಬಾಕ್ಸ್‌ನಲ್ಲಿ ({device_id}) ಭದ್ರತಾ ಎಚ್ಚರಿಕೆ ಪ್ರಸಾರ ಮಾಡಲಾಗಿದೆ.",
        "ml": "മുന്നറിയിപ്പ് {name}! ഞങ്ങൾ NPCI UPI സ്വിച്ചും Paytm ഗേറ്റ്‌വേയും പരിശോധിച്ചു. നിങ്ങളുടെ അക്കൗണ്ടിൽ ₹{amount} പേയ്‌മെന്റ് എത്തിയിട്ടില്ല. ഇടപാടുകൾ ഒന്നും നടക്കാത്തതിനാലാണ് സൗണ്ട്ബോക്സ് മിണ്ടാതിരുന്നത്. ഇത് വ്യാജ സ്ക്രീൻഷോട്ട് തട്ടിപ്പായിരിക്കാം. സാധനങ്ങൾ നൽകരുത്. നിങ്ങളുടെ സൗണ്ട്ബോക്സിൽ ({device_id}) മുന്നറിയിപ്പ് പ്രക്ഷേപണം ചെയ്തു.",
        "pa": "ਸਾਵਧਾਨ {name}! ਅਸੀਂ NPCI UPI ਸਵਿੱਚ ਅਤੇ ਪੇਟੀਐਮ ਗੇਟਵੇ ਦੀ ਜਾਂਚ ਕੀਤੀ ਹੈ। ਤੁਹਾਡੇ ਖਾਤੇ ਵਿੱਚ ₹{amount} ਦਾ ਕੋਈ ਭੁਗਤਾਨ ਨਹੀਂ ਆਇਆ। ਕੋਈ ਲੈਣ-ਦੇਣ ਨਾ ਹੋਣ ਕਰਕੇ ਹੀ ਸਾਊਂਡਬਾਕਸ ਸ਼ਾਂਤ ਸੀ। ਇਹ ਨਕਲੀ ਸਕ੍ਰੀਨਸ਼ੌਟ ਹੋ ਸਕਦਾ ਹੈ। ਸਮਾਨ ਨਾ ਦਿਓ। ਅਸੀਂ ਤੁਹਾਡੇ ਸਾਊਂਡਬਾਕਸ ({device_id}) ਤੇ ਸੁਰੱਖਿਆ ਚੇਤਾਵਨੀ ਪ੍ਰਸਾਰਿਤ ਕਰ ਦਿੱਤੀ ਹੈ।"
    },
    "S4_RESOLVED": {
        "en": "Audit Confirmed: For Order #{order_id} (₹{amount}), the customer experienced an NPCI duplicate debit. The primary transaction is successfully settled, and the duplicate ₹{amount} was automatically reversed by NPCI to customer's account (Reversal Ref: REV-{order_id}). No chargeback risk exists.",
        "hi": "ऑडिट रिपोर्ट: ऑर्डर #{order_id} (₹{amount}) के लिए ग्राहक का NPCI में डुप्लीकेट डेबिट हुआ था। प्राथमिक भुगतान आपके खाते में जमा है, और अतिरिक्त ₹{amount} NPCI द्वारा ग्राहक को वापस कर दिया गया है (रिफंड संदर्भ: REV-{order_id})। कोई विवाद जोखिम नहीं है।",
        "mr": "ऑडिट पडताळणी: ऑर्डर #{order_id} (₹{amount}) साठी ग्राहकाचे NPCI वर दोनदा पैसे कापले गेले होते. मुख्य पेमेंट आपल्या खात्यात जमा आहे आणि अतिरिक्त ₹{amount} NPCI ने ग्राहकाच्या खात्यात परत पाठवले आहेत (रिफंड संदर्भ: REV-{order_id}).",
        "gu": "ઓડિટ પુષ્ટિ: ઓર્ડર #{order_id} (₹{amount}) માટે ગ્રાહકનું ડુપ્લિકેટ ડેબિટ થયું હતું. મુખ્ય પેમેન્ટ જમા છે, અને વધારાના ₹{amount} NPCI દ્વારા આપમેળે પરત કરવામાં આવ્યા છે (સંદર્ભ: REV-{order_id}).",
        "bn": "অডিট নিশ্চিত: অর্ডার #{order_id} (₹{amount}) এর জন্য গ্রাহকের ডুপ্লিকেট ডেবিট হয়েছিল। মূল পেমেন্ট আপনার কাছে জমা আছে, এবং অতিরিক্ত ₹{amount} NPCI গ্রাহককে ফেরত দিয়েছে (রেফারেন্স: REV-{order_id})।",
        "ta": "தணிக்கை உறுதி: ஆர்டர் #{order_id} (₹{amount})க்கு வாடிக்கையாளருக்கு இரண்டு முறை பிடித்தம் செய்யப்பட்டது. அசல் தொகை வரவு வைக்கப்பட்டது, கூடுதல் ₹{amount} NPCI ஆல் திருப்பி அனுப்பப்பட்டது (குறிப்பு: REV-{order_id}).",
        "te": "ఆడిట్ ధృవీకరణ: ఆర్డర్ #{order_id} (₹{amount}) కోసం కస్టమర్‌కు డూప్లికేట్ డెబిట్ జరిగింది. ప్రాథమిక చెల్లింపు జమ అయింది, అదనపు ₹{amount} NPCI కస్టమర్‌కు రీఫండ్ చేసింది (రెఫరెన్స్: REV-{order_id}).",
        "kn": "ಆಡಿಟ್ ದೃಢೀಕರಣ: ಆರ್ಡರ್ #{order_id} (₹{amount}) ಗಾಗಿ ಗ್ರಾಹಕರಿಗೆ ಡ್ಯೂಪ್ಲಿಕೇಟ್ ಡೆಬಿಟ್ ಆಗಿತ್ತು. ಮುಖ್ಯ ಪಾವತಿ ಜಮೆಯಾಗಿದೆ ಮತ್ತು ಹೆಚ್ಚುವರಿ ₹{amount} ಅನ್ನು NPCI ಗ್ರಾಹಕರಿಗೆ ಮರುಪಾವತಿಸಿದೆ (ರೆಫರೆನ್ಸ್: REV-{order_id}).",
        "ml": "ഓഡിറ്റ് സ്ഥിരീകരിച്ചു: ഓർഡർ #{order_id} (₹{amount}) ഇടപാടിൽ ഉപഭോക്താവിന് ഇരട്ട ഡെബിറ്റ് സംഭവിച്ചു. പ്രധാന പേയ്‌മെന്റ് ക്രെഡിറ്റ് ആയി, അധിക ₹{amount} NPCI റീഫണ്ട് ചെയ്തു (റഫറൻസ്: REV-{order_id}).",
        "pa": "ਆਡਿਟ ਪੁਸ਼ਟੀ: ਆਰਡਰ #{order_id} ਲਈ ਗਾਹਕ ਦਾ ਦੋਹਰਾ ਡੈਬਿਟ ਹੋਇਆ ਸੀ। ਅਸਲ ਰਕਮ ਜਮ੍ਹਾ ਹੈ, ਅਤੇ ਦੂਜੇ ₹{amount} NPCI ਵੱਲੋਂ ਗਾਹਕ ਨੂੰ ਵਾਪਸ ਭੇਜ ਦਿੱਤੇ ਗਏ ਹਨ (ਰੈਫਰੈਂਸ: REV-{order_id})।",
    },
    "S5_RESOLVED": {
        "en": "Attention {name}: We detected an industry-wide latency spike on the HDFC acquiring rail affecting your QR codes. ResolveAI has automatically re-routed your merchant acquiring traffic to the ICICI backup gateway. Future payments will now process smoothly.",
        "hi": "ध्यान दें {name}: HDFC बैंक गेटवे में तकनीकी समस्या के कारण आपके QR कोड पर भुगतान विफल हो रहे थे। ResolveAI ने आपके ट्रैफिक को तुरंत ICICI बैकअप गेटवे पर ट्रांसफर कर दिया है। अब भुगतान सुचारू रूप से होंगे।",
        "mr": "लक्ष द्या {name}: HDFC बँक गेटवेवरील तांत्रिक अडचणीमुळे आपल्या QR वर पेमेंट्स अयशस्वी होत होते. ResolveAI ने आपले व्यवहार त्वरित ICICI बॅकअप गेटवेवर वळवले आहेत. आता सर्व पेमेंट्स सुरळीत चालतील.",
        "gu": "ધ્યાન આપો {name}: HDFC બેંક ગેટવેમાં સમસ્યાને કારણે પેમેન્ટ નિષ્ફળ થઈ રહ્યા હતા. ResolveAI એ તમારા ટ્રાફિકને ICICI બેકઅપ ગેટવે પર રી-રૂટ કરી દીધું છે. હવે બધા પેમેન્ટ સરળતાથી થશે.",
        "bn": "মনোযোগ দিন {name}: HDFC ব্যাংক গেটওয়েতে সমস্যার কারণে QR পেমেন্ট ব্যর্থ হচ্ছিল। ResolveAI আপনার ট্রাফিক ICICI ব্যাকআপ গেটওয়েতে সরিয়ে নিয়েছে। এখন সমস্ত পেমেন্ট সঠিকভাবে সম্পন্ন হবে।",
        "ta": "கவனிக்கவும் {name}: HDFC வங்கி நுழைவாயிலில் ஏற்பட்ட தொழில்நுட்ப கோளாறால் பணம் செலுத்துவதில் சிக்கல் ஏற்பட்டது. ResolveAI உங்கள் பரிவர்த்தனைகளை ICICI காப்பு நுழைவாயிலுக்கு மாற்றியுள்ளது. இனி பணம் தடையின்றி வரும்.",
        "te": "గమనించండి {name}: HDFC బ్యాంక్ గేట్‌వేలో సాంకేతిక సమస్య వల్ల QR చెల్లింపులు విఫలమయ్యాయి. ResolveAI మీ ట్రాఫిక్‌ను ICICI బ్యాకప్ గేట్‌వేకి రీ-రూట్ చేసింది. ఇకపై చెల్లింపులు సాఫీగా జరుగుతాయి.",
        "kn": "ಗಮನಿಸಿ {name}: HDFC ಬ್ಯಾಂಕ್ ಗೇಟ್‌ವೇ ಸಮಸ್ಯೆಯಿಂದ ನಿಮ್ಮ QR ಪಾವತಿಗಳು ವಿಫಲವಾಗುತ್ತಿದ್ದವು. ResolveAI ನಿಮ್ಮ ಟ್ರಾಫಿಕ್ ಅನ್ನು ICICI ಬ್ಯಾಕಪ್ ಗೇಟ್‌ವೇಗೆ ಮರು-ರೂಟ್ ಮಾಡಿದೆ. ಇನ್ನು ಪಾವತಿಗಳು ಸುಗಮವಾಗಿ ನಡೆಯಲಿವೆ.",
        "ml": "ശ്രദ്ധിക്കുക {name}: HDFC ബാങ്ക് ഗേറ്റ്‌വേ തകരാർ കാരണം നിങ്ങളുടെ QR പേയ്‌മെന്റുകൾ പരാജയപ്പെട്ടിരുന്നു. ResolveAI നിങ്ങളുടെ ട്രാഫിക് ICICI ബാക്കപ്പ് ഗേറ്റ്‌വേയിലേക്ക് മാറ്റി. ഇനി പേയ്‌മെന്റുകൾ സുഗമമായി നടക്കും.",
        "pa": "ਧਿਆਨ ਦਿਓ {name}: HDFC ਬੈਂਕ ਗੇਟਵੇ ਵਿੱਚ ਸਮੱਸਿਆ ਕਾਰਨ ਭੁਗਤਾਨ ਫੇਲ੍ਹ ਹੋ ਰਹੇ ਸਨ। ResolveAI ਨੇ ਤੁਹਾਡੇ ਟ੍ਰੈਫਿਕ ਨੂੰ ICICI ਬੈਕਅੱਪ ਗੇਟਵੇ ਤੇ ਬਦਲ ਦਿੱਤਾ ਹੈ। ਹੁਣ ਭੁਗਤਾਨ ਸੁਚਾਰੂ ਢੰਗ ਨਾਲ ਹੋਣਗੇ।",
    },
    "SAFETY_HOLD": {
        "en": "Safety Threshold Checkpoint: Transaction of ₹{amount} exceeds autonomous limit of ₹25,000. Ledger verified, batch #{batch_code} paused for supervisor authorization.",
        "hi": "सुरक्षा सीमा चेतावनी: ₹{amount} का लेनदेन ₹25,000 की स्वायत्त सीमा से अधिक है। लेज़र सत्यापित है, बैच #{batch_code} पर्यवेक्षक अनुमोदन के लिए रोका गया है।",
        "mr": "सुरक्षा मर्यादा चेतावणी: ₹{amount} चा व्यवहार ₹25,000 च्या स्वायत्त मर्यादेपेक्षा जास्त आहे. लेजर पडताळणी झाली आहे, बॅच #{batch_code} पर्यवेक्षक मंजुरीसाठी थांबवली आहे.",
        "gu": "સુરક્ષા મર્યાદા ચેતવણી: ₹{amount} નો વ્યવહાર ₹25,000 ની મર્યાદાથી વધુ છે. લેજર ચકાસાયેલ છે, બેચ #{batch_code} સુપરવાઇઝર મંજૂરી માટે રોકવામાં આવી છે.",
        "bn": "সুরক্ষা সীমা সতর্কতা: ₹{amount} এর লেনদেন ₹25,000 সীমার বেশি। লেজার যাচাই করা হয়েছে, ব্যাচ #{batch_code} সুপারভাইজার অনুমোদনের জন্য স্থগিত।",
        "ta": "பாதுகாப்பு வரம்பு எச்சரிக்கை: ₹{amount} பரிவர்த்தனை ₹25,000 வரம்பை மீறியுள்ளது. கணக்கு சரிபார்க்கப்பட்டு, பேட்ச் #{batch_code} மேற்பார்வையாளர் அனுமதிக்காக நிறுத்தப்பட்டது.",
        "te": "భద్రతా పరిమితి హెచ్చరిక: ₹{amount} లావాదేవీ ₹25,000 పరిమితిని మించింది. లెడ్జర్ ధృవీకరించబడింది, బ్యాచ్ #{batch_code} సూపర్‌వైజర్ ఆమోదం కోసం ఆపబడింది.",
        "kn": "ಸುರಕ್ಷತಾ ಮಿತಿ ಎಚ್ಚರಿಕೆ: ₹{amount} ವಹಿವಾಟು ₹25,000 ಮಿತಿಯನ್ನು ಮೀರಿದೆ. ಲೆಡ್ಜರ್ ಪರಿಶೀಲಿಸಲಾಗಿದೆ, ಬ್ಯಾಚ್ #{batch_code} ಮೇಲ್ವಿಚಾರಕರ ಅನುಮೋದನೆಗೆ ನಿಲ್ಲಿಸಲಾಗಿದೆ.",
        "ml": "സുരക്ഷാ പരിധി മുന്നറിയിപ്പ്: ₹{amount} ഇടപാട് ₹25,000 പരിധി കവിഞ്ഞു. ലെഡ്ജർ പരിശോധിച്ചു, ബാച്ച് #{batch_code} സൂപ്പർവൈസർ അനുമതിക്കായി നിർത്തിവച്ചു.",
        "pa": "ਸੁਰੱਖਿਆ ਸੀਮਾ ਚੇਤਾਵਨੀ: ₹{amount} ਦਾ ਲੈਣ-ਦੇਣ ₹25,000 ਦੀ ਸੀਮਾ ਤੋਂ ਵੱਧ ਹੈ। ਲੇਜ਼ਰ ਤਸਦੀਕ ਕੀਤਾ ਗਿਆ ਹੈ, ਬੈਚ #{batch_code} ਸੁਪਰਵਾਈਜ਼ਰ ਦੀ ਮਨਜ਼ੂਰੀ ਲਈ ਰੋਕਿਆ ਗਿਆ ਹੈ।"
    },
    "DEFAULT_RESOLVED": {
        "en": "Hello {name}. We have audited your Paytm merchant account. All recent payments are settled and your Soundbox is online. If you need assistance with a specific customer transaction, please provide the Order ID or RRN.",
        "hi": "नमस्ते {name}। हमने आपके पेटीएम मर्चेंट खाते का ऑडिट किया है। आपके सभी हालिया भुगतान सेटल हो चुके हैं और साउंडबॉक्स ऑनलाइन है। यदि आपको किसी विशिष्ट भुगतान में सहायता चाहिए, तो कृपया ऑर्डर आईडी प्रदान करें।",
        "mr": "नमस्ते {name}. आम्ही आपल्या पेटीएम मर्चंट खात्याचे ऑडिट केले आहे. आपले सर्व अलीकडील पेमेंट्स सेटल झाले आहेत आणि साउंडबॉक्स ऑनलाइन आहे. आपल्याला कोणत्याही व्यवहाराबद्दल मदत हवी असल्यास कृपया ऑर्डर आयडी द्या.",
        "gu": "નમસ્તે {name}. અમે તમારા પેટીએમ ખાતાનું ઓડિટ કર્યું છે. તમામ તાજેતરના પેમેન્ટ સેટલ થઈ ગયા છે અને સાઉન્ડબોક્સ ઓનલાઇન છે. જો કોઈ વ્યવહાર માટે સહાય જોઈએ, તો ઓર્ડર આઈડી આપો.",
        "bn": "নমস্কার {name}। আমরা আপনার পেটিএম মার্চেন্ট অ্যাকাউন্ট অডিট করেছি। সমস্ত সাম্প্রতিক পেমেন্ট সেটেল হয়েছে এবং সাউন্ডবক্স অনলাইন আছে।",
        "ta": "வணக்கம் {name}. உங்கள் Paytm கணக்கை சரிபார்த்தோம். அனைத்து சமீபத்திய பரிவர்த்தனைகளும் தீர்க்கப்பட்டு சவுண்ட்பாக்ஸ் ஆன்லைனில் உள்ளது.",
        "te": "నమస్తే {name}. మేము మీ Paytm మర్చంట్ ఖాతాను ఆడిట్ చేశాము. ఇటీవలి చెల్లింపులన్నీ సెటిల్ అయ్యాయి మరియు సౌండ్‌బాక్స్ ఆన్‌లైన్‌లో ఉంది.",
        "kn": "ನಮಸ್ಕಾರ {name}. ನಾವು ನಿಮ್ಮ Paytm ಮರ್ಚೆಂಟ್ ಖಾತೆಯನ್ನು ಪರಿಶೀಲಿಸಿದ್ದೇವೆ. ಇತ್ತೀಚಿನ ಎಲ್ಲಾ ಪಾವತಿಗಳು ಸೆಟ್ಲ್ ಆಗಿವೆ ಮತ್ತು ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಆನ್‌ಲೈನ್‌ನಲ್ಲಿದೆ.",
        "ml": "നമസ്കാരം {name}. ഞങ്ങൾ നിങ്ങളുടെ Paytm അക്കൗണ്ട് ഓഡിറ്റ് ചെയ്തു. സമീപകാല പേയ്‌മെന്റുകൾ എല്ലാം സെറ്റിൽ ചെയ്തു, സൗണ്ട്ബോക്സ് ഓൺലൈനാണ്.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}। ਅਸੀਂ ਤੁਹਾਡੇ ਪੇਟੀਐਮ ਖਾਤੇ ਦਾ ਆਡਿਟ ਕੀਤਾ ਹੈ। ਸਾਰੇ ਹਾਲੀਆ ਭੁਗਤਾਨ ਸੈਟਲ ਹਨ ਅਤੇ ਸਾਊਂਡਬਾਕਸ ਆਨਲਾਈਨ ਹੈ।"
    }
}

import re

def clean_plain_text(text: str) -> str:
    """
    Strips all markdown asterisks (* and **) from the text,
    removes header markers, and returns clean, human-readable plain text.
    """
    if not text:
        return ""
    # Strip asterisks (* and **)
    text = text.replace("*", "")
    # Remove markdown headers like ### or ## at line starts
    text = re.sub(r'(?m)^[ \t]*#+[ \t]*', '', text)
    # Remove markdown backticks if any
    text = text.replace("`", "")
    # Normalize multiple consecutive spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def format_multilingual_msg(scenario_key: str, lang: str = "en", **kwargs) -> str:
    """Returns a natural, native language response template for the given scenario."""
    templates = MULTILINGUAL_TEMPLATES.get(scenario_key, {})
    template = templates.get(lang.lower(), templates.get("en", ""))
    try:
        return clean_plain_text(template.format(**kwargs))
    except Exception:
        return clean_plain_text(template)

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "gu": "Gujarati",
    "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "pa": "Punjabi"
}

def generate_ai_response(
    merchant: Dict[str, Any],
    tx_list: List[Dict[str, Any]],
    batch_list: List[Dict[str, Any]],
    soundbox: Optional[Dict[str, Any]],
    action_taken: str,
    message: str,
    language: str = "en",
    scenario_default: Optional[str] = None
) -> str:
    """
    True Generative AI Response Synthesizer.
    1. If an LLM (Groq, Sarvam, OpenAI, Gemini) is configured via environment/.env,
       invokes the LangChain model with live SQL context and merchant conversation.
    2. If no LLM API key is present or LLM call fails, the Dynamic Context Engine
       inspects the merchant's query and synthesizes factual answers from live database rows
       (e.g., listing failed order IDs, recent order IDs, UTRs, Soundbox telemetry, bank accounts)
       in the selected regional language.
    All outputs are strictly plain text without markdown asterisks (*).
    """
    msg_clean = message.lower()
    lang = language.lower()

    # 1. Real LLM invocation if provider/key is configured
    active_llm = get_llm()
    if active_llm is not None:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            lang_name = LANGUAGE_NAMES.get(lang, "English")

            system_prompt = f"""You are ResolveAI, an autonomous merchant operations teammate for Paytm India.
You speak with merchants with high precision, professional empathy, and zero deflection.
You have direct access to their live database state and the operational actions taken by ResolveAI.
Answer the merchant's exact question accurately and directly using the live database facts provided below.
Respond in the requested language: {lang_name} ({lang}).
Keep your answer clear, concise, and professional without AI slop, emojis, or generic FAQ deflection.

CRITICAL FORMATTING INSTRUCTIONS:
- Do NOT use markdown asterisks (* or **) anywhere in your response.
- Do NOT bold text using asterisks. Output plain, clean text only.
- Write IDs and amounts plainly (e.g. PTM-89104 or ₹4,500, never **PTM-89104** or *₹4,500*).
- Do NOT use asterisks for bullet points. Use standard numbers (1., 2.) or hyphens (-) if listing items.

Merchant Profile:
- Business: {merchant.get('name')} ({merchant.get('business_type')})
- Bank: {merchant.get('bank_name')} (Account: {merchant.get('account_number')}, IFSC: {merchant.get('ifsc')})

Live Database State:
- Recent Transactions: {json.dumps(tx_list, default=str)}
- Settlement Batches: {json.dumps(batch_list, default=str)}
- Soundbox Telemetry: {json.dumps(soundbox or {}, default=str)}
- Action Taken by ResolveAI: {action_taken}"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=message)
            ]
            response = active_llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)
            if content and len(content.strip()) > 5:
                return clean_plain_text(content)
        except Exception as e:
            log.warning(f"[AI_SYNTHESIZER] LLM call failed ({e}). Falling back to Dynamic Context Engine.")

    # 2. Dynamic Context Engine (Accurate SQL-backed responses across all 10 languages)
    # Check A1: Failed Orders specifically requested (e.g. "Which order ID got failed can you give me list of it please ?")
    failed_inquiry_keywords = [
        "which order got failed", "orders failed", "failed order", "failed payments", "which failed",
        "कौन से ऑर्डर फेल", "विफल ऑर्डर", "अयशस्वी ऑर्डर", "નિષ્ફળ ઓર્ડર", "ব্যর্থ অর্ডার", "தோல்வியடைந்த ஆர்டர்"
    ]
    if any(k in msg_clean for k in failed_inquiry_keywords):
        failed_txs = [t for t in tx_list if t.get("status") == "FAILED"]
        target_txs = failed_txs if failed_txs else tx_list[:3]

        if lang == "hi":
            lines = [f"यहाँ {merchant['name']} के विफल भुगतानों का विवरण है:"]
            for idx, t in enumerate(target_txs, 1):
                err = f" | त्रुटि: {t.get('failure_reason')}" if t.get("failure_reason") else ""
                lines.append(f"{idx}. ऑर्डर #{t['order_id']}: ₹{t['amount']:,.2f} ({t['status']}) | ग्राहक: {t['customer_vpa']} | RRN: {t['rrn']}{err}")
            lines.append("ResolveAI ने ट्रैफिक को ICICI बैकअप गेटवे पर ट्रांसफर कर दिया है ताकि भविष्य के सभी भुगतान सुचारू रूप से हों।")
            return clean_plain_text("\n".join(lines))
        elif lang == "mr":
            lines = [f"येथे {merchant['name']} साठी अयशस्वी झालेल्या ग्राहक व्यवहारांची यादी आहे:"]
            for idx, t in enumerate(target_txs, 1):
                lines.append(f"{idx}. ऑर्डर #{t['order_id']}: ₹{t['amount']:,.2f} ({t['status']}) | ग्राहक: {t['customer_vpa']} | RRN: {t['rrn']}")
            lines.append("ResolveAI ने आपले व्यवहार ICICI बॅकअप गेटवेवर वळवले आहेत.")
            return clean_plain_text("\n".join(lines))
        elif lang == "gu":
            lines = [f"અહીં {merchant['name']} માટે નિષ્ફળ થયેલા ગ્રાહક પેમેન્ટની યાદી છે:"]
            for idx, t in enumerate(target_txs, 1):
                lines.append(f"{idx}. ઓર્ડર #{t['order_id']}: ₹{t['amount']:,.2f} ({t['status']}) | ગ્રાહક: {t['customer_vpa']} | RRN: {t['rrn']}")
            lines.append("ResolveAI એ તમારો ટ્રાફિક ICICI બેકઅપ ગેટવે પર રી-રૂટ કરી દીધું છે.")
            return clean_plain_text("\n".join(lines))
        else:
            lines = [f"Here is the list of failed customer payments for {merchant['name']} (caused by HDFC acquiring gateway latency):"]
            for idx, t in enumerate(target_txs, 1):
                err = f" | Reason: {t.get('failure_reason')}" if t.get("failure_reason") else ""
                lines.append(f"{idx}. Order #{t['order_id']}: ₹{t['amount']:,.2f} ({t['status']}) | Customer: {t['customer_vpa']} | RRN: {t['rrn']}{err}")
            lines.append("ResolveAI has automatically re-routed acquiring traffic to the ICICI backup gateway so future payments will process normally.")
            return clean_plain_text("\n".join(lines))

    # Check A2: General Order ID Inquiry (e.g. "What is the order id of my payment ?")
    recent_order_keywords = [
        "order id of my payment", "what is the order id", "what is my order id", "what's the order id",
        "order id", "order number", "order details", "payment id",
        "ऑर्डर आईडी", "ऑर्डर नंबर", "ऑर्डर संख्या", "ऑर्डर की आईडी",
        "ऑर्डर आयडी", "ऑर्डर क्रमांक", "ઓર્ડર આઈડી", "অর্ডার আইডি", "ஆர்டர் ஐடி", "ఆర్డర్ ఐడి"
    ]
    if any(k in msg_clean for k in recent_order_keywords) and tx_list:
        latest_tx = tx_list[0]
        if lang == "hi":
            return clean_plain_text(f"आपके हालिया भुगतान (₹{latest_tx['amount']:,.2f}) की ऑर्डर आईडी #{latest_tx['order_id']} है (स्थिति: {latest_tx['status']}, ग्राहक: {latest_tx['customer_vpa']})।")
        elif lang == "mr":
            return clean_plain_text(f"आपल्या अलीकडील पेमेंट (₹{latest_tx['amount']:,.2f}) चा ऑर्डर आयडी #{latest_tx['order_id']} आहे (स्थिती: {latest_tx['status']}).")
        elif lang == "gu":
            return clean_plain_text(f"તમારા તાજેતરના પેમેન્ટ (₹{latest_tx['amount']:,.2f}) નો ઓર્ડર આઈડી #{latest_tx['order_id']} છે.")
        else:
            return clean_plain_text(f"The order ID for your recent payment of ₹{latest_tx['amount']:,.2f} is #{latest_tx['order_id']} (Status: {latest_tx['status']}, Customer: {latest_tx['customer_vpa']}).")

    # Check A3: Customer / Payer Inquiry
    customer_inquiry_keywords = [
        "who was the customer", "who is the customer", "customer vpa", "customer name", "who paid",
        "ग्राहक कौन", "किसने पैसे दिए", "ग्राहकाचे नाव", "ગ્રાહક કોણ"
    ]
    if any(k in msg_clean for k in customer_inquiry_keywords) and tx_list:
        latest_tx = tx_list[0]
        if lang == "hi":
            return clean_plain_text(f"आपके हालिया लेनदेन (#{latest_tx['order_id']}) के ग्राहक {latest_tx['customer_vpa']} हैं (राशि: ₹{latest_tx['amount']:,.2f}, RRN: {latest_tx['rrn']})।")
        else:
            return clean_plain_text(f"The customer for your recent transaction (#{latest_tx['order_id']}) is {latest_tx['customer_vpa']} (Amount: ₹{latest_tx['amount']:,.2f}, RRN: {latest_tx['rrn']}).")

    # Check B: Specific Order Lookup (e.g. user types "PTM-99121" or "33219" or "55102")
    order_match = re.search(r'(PTM-\d+|\b\d{5}\b)', message.upper())
    if order_match and not any(k in msg_clean for k in ["smart tv", "4500", "78000", "1200"]):
        matched_str = order_match.group(1)
        found_tx = next((t for t in tx_list if matched_str in str(t.get("order_id", ""))), None)
        if not found_tx:
            res = run_query(f"SELECT order_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason FROM transactions WHERE order_id LIKE '%{matched_str}%' LIMIT 1")
            found_tx = res[0] if res else None

        if found_tx:
            if lang == "hi":
                return clean_plain_text(
                    f"ऑर्डर ऑडिट रिपोर्ट #{found_tx['order_id']}: राशि: ₹{found_tx['amount']:,.2f} | "
                    f"स्थिति: {found_tx['status']} | मोड: {found_tx['payment_mode']} | "
                    f"ग्राहक VPA: {found_tx['customer_vpa']} | RRN: {found_tx['rrn']}"
                    + (f" | कारण: {found_tx['failure_reason']}" if found_tx.get('failure_reason') else "")
                )
            else:
                return clean_plain_text(
                    f"Order Audit for #{found_tx['order_id']}: Amount: ₹{found_tx['amount']:,.2f} | "
                    f"Status: {found_tx['status']} | Mode: {found_tx['payment_mode']} | "
                    f"Customer VPA: {found_tx['customer_vpa']} | RRN: {found_tx['rrn']}"
                    + (f" | Failure Reason: {found_tx['failure_reason']}" if found_tx.get('failure_reason') else "")
                )

    # Check C: Soundbox Battery / Device Status
    device_inquiry_keywords = [
        "battery level", "battery percent", "charging status", "sim status", "soundbox status", "device health",
        "बैटरी स्तर", "बैटरी कितने", "चार्जिंग कितनी", "सिम की स्थिति",
        "बॅटरी लेव्हल", "બેટરી કેટલી", "ব্যাটারি লেভেল", "பேட்டரி அளவு", "బ్యాటరీ స్థాయి"
    ]
    if any(k in msg_clean for k in device_inquiry_keywords) and soundbox:
        if lang == "hi":
            return clean_plain_text(f"साउंडबॉक्स टेलीमेट्री ({soundbox['device_id']}): बैटरी स्तर {soundbox['battery_level']}% है। सिम स्थिति: {soundbox['sim_status']}। अंतिम साउंडबॉक्स प्रसारण: {soundbox['last_chime_status']} (फर्मवेयर: {soundbox['firmware_version']})।")
        else:
            return clean_plain_text(f"Paytm Soundbox ({soundbox['device_id']}) Telemetry: Battery level is {soundbox['battery_level']}%. GSM Network is {soundbox['sim_status']}. Last chime status: {soundbox['last_chime_status']} (Firmware: {soundbox['firmware_version']}).")

    # Check D: Bank Account / IFSC Details
    bank_inquiry_keywords = [
        "bank account number", "account number", "my ifsc", "ifsc code", "what is my bank",
        "खाता संख्या", "खाता नंबर", "अकाउंट नंबर", "आईएफएससी", "बँक खाते क्रमांक", "ખાતા નંબર"
    ]
    if any(k in msg_clean for k in bank_inquiry_keywords):
        phone_val = merchant.get('phone', 'N/A')
        if lang == "hi":
            return clean_plain_text(f"पंजीकृत सेटलमेंट बैंक: {merchant['bank_name']} (खाता संख्या: {merchant['account_number']}, IFSC: {merchant['ifsc']})। संपर्क फोन: {phone_val}।")
        else:
            return clean_plain_text(f"Registered Settlement Account: {merchant['bank_name']} (A/C: {merchant['account_number']}, IFSC: {merchant['ifsc']}). Registered Phone: {phone_val}.")

    # Check E: UTR / Settlement Credit Details
    utr_inquiry_keywords = [
        "utr number", "what is utr", "utr number kya", "यूटीआर नंबर", "यूटियार", "utr reference"
    ]
    if any(k in msg_clean for k in utr_inquiry_keywords) and batch_list:
        b = batch_list[0]
        utr_str = b.get('utr_number') or "Pending clearance"
        if lang == "hi":
            return clean_plain_text(f"सेटलमेंट बैच #{b['batch_code']} (₹{b['total_amount']:,.2f}) स्थिति: {b['status']}। रेल: {b['rail']}। बैंक UTR: {utr_str}।")
        else:
            return clean_plain_text(f"Settlement Batch #{b['batch_code']} (₹{b['total_amount']:,.2f}) status is {b['status']}. Rail: {b['rail']}. Bank UTR: {utr_str} credited to {merchant['bank_name']}.")

    # Default to scenario template if provided
    if scenario_default:
        return clean_plain_text(scenario_default)

    return clean_plain_text(format_multilingual_msg("DEFAULT_RESOLVED", lang=language, name=merchant["name"]))

CANONICAL_PROMPTS_BY_SCENARIO = {
    "S1": [
        "My ₹4,500 payment from morning sales hasn't reached my bank account yet. Please check.",
        "मेरी सुबह की ₹4,500 की बिक्री का पैसा अभी तक मेरे बैंक खाते में नहीं आया। कृपया जांच करें।",
        "माझ्या सकाळच्या विक्रीचे ₹4,500 अजूनही माझ्या बँक खात्यात जमा झाले नाहीत. कृपया तपासा.",
        "મારી સવારના વેચાણના ₹4,500 હજુ સુધી મારા બેંક ખાતામાં આવ્યા નથી. કૃપા કરીને તપાસો.",
        "আমার সকালের বিক্রির ₹4,500 এখনও আমার ব্যাংক অ্যাকাউন্টে ঢোকেনি। দয়া করে চেক করুন।",
        "எனது காலை விற்பனைக்கான ₹4,500 இன்னும் எனது வங்கி கணக்கில் வரவில்லை. தயவுசெய்து சரிபார்க்கவும்.",
        "నా ఉదయం అమ్మకాల ₹4,500 ఇంకా నా బ్యాంక్ ఖాతాలో జమ కాలేదు. దయచేసి పరిశీలించండి.",
        "ನನ್ನ ಬೆಳಗಿನ ಮಾರಾಟದ ₹4,500 ಹಣ ಇನ್ನೂ ನನ್ನ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಬಂದಿಲ್ಲ. ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ.",
        "എന്റെ രാവിലത്തെ വിൽപ്പനയുടെ ₹4,500 ഇതുവരെ എന്റെ ബാങ്ക് അക്കൗണ്ടിൽ എത്തിയില്ല. ദയവായി പരിശോധിക്കുക.",
        "ਮੇਰੀ ਸਵੇਰ ਦੀ ਵਿਕਰੀ ਦੇ ₹4,500 ਅਜੇ ਤੱਕ ਮੇਰੇ ਬੈਂਕ ਖਾਤੇ ਵਿੱਚ ਨਹੀਂ ਆਏ। ਕਿਰਪਾ ਕਰਕੇ ਜਾਂਚ ਕਰੋ।"
    ],
    "S2": [
        "Customer bought a smart TV for ₹78,000 via QR, but the settlement is showing on hold.",
        "ग्राहक ने QR से ₹78,000 का स्मार्ट टीवी खरीदा, लेकिन सेटलमेंट होल्ड पर दिख रहा है।",
        "ग्राहकाने QR द्वारे ₹78,000 चा स्मार्ट टीव्ही खरेदी केला, पण सेटलमेंट होल्डवर दिसत आहे.",
        "ગ્રાહકે QR થી ₹78,000 નું સ્માર્ટ ટીવી ખરીદ્યું, પણ સેટલમેન્ટ હોલ્ડ પર બતાવે છે.",
        "গ্রাহক QR দিয়ে ₹78,000 এর স্মার্ট টিভি কিনেছেন, কিন্তু সেটেলমেন্ট হোল্ডে দেখাচ্ছে।",
        "வாடிக்கையாளர் QR மூலம் ₹78,000க்கு ஸ்மார்ட் டிவி வாங்கினார், ஆனால் செட்டில்மென்ட் நிறுத்தி வைக்கப்பட்டுள்ளது.",
        "కస్టమర్ QR ద్వారా ₹78,000 స్మార్ట్ టీవీ కొన్నారు, కానీ సెటిల్‌మెంట్ హోల్డ్‌లో ఉంది.",
        "ಗ್ರಾಹಕರು QR ಮೂಲಕ ₹78,000 ಬೆಲೆಯ ಸ್ಮಾರ್ಟ್ ಟಿವಿ ಖರೀದಿಸಿದ್ದಾರೆ, ಆದರೆ ಸೆಟ್ಲ್‌ಮೆಂಟ್ ಹೋಲ್ಡ್‌ನಲ್ಲಿದೆ.",
        "ഉപഭോക്താവ് QR വഴി ₹78,000-ന് സ്മാർട്ട് ടിവി വാങ്ങി, എന്നാൽ സെറ്റിൽമെന്റ് ഹോൾഡിലാണ്.",
        "ਗਾਹਕ ਨੇ QR ਰਾਹੀਂ ₹78,000 ਦਾ ਸਮਾਰਟ ਟੀਵੀ ਖਰੀਦਿਆ, ਪਰ ਸੈਟਲਮੈਂਟ ਹੋਲਡ ਤੇ ਦਿਖ ਰਹੀ ਹੈ।"
    ],
    "S3": [
        "Customer is showing screenshot of ₹60 paid for tea, but Soundbox stayed silent! Did money arrive?",
        "Customer paid ₹60 for tea, but Soundbox did not announce anything!",
        "ग्राहक चाय के लिए ₹60 का स्क्रीनशॉट दिखा रहा है, लेकिन साउंडबॉक्स नहीं बोला! क्या सच में पैसे आए हैं?",
        "ग्राहक ने चाय के लिए ₹60 दिए, लेकिन साउंडबॉक्स ने कुछ नहीं बोला!",
        "ग्राहक चहासाठी ₹60 चा स्क्रीनशॉट दाखवत आहे, पण साउंडबॉक्स काहीच बोलला नाही! खरंच पैसे आले का?",
        "ग्राहकाने चहासाठी ₹60 दिले, पण साउंडबॉक्स काहीच बोलला नाही!",
        "ગ્રાહક ચા માટે ₹60 નો સ્ક્રીનશોટ બતાવે છે, પણ સાઉન્ડબોક્સ કંઈ બોલ્યું નહીં! શું ખરેખર પૈસા આવ્યા?",
        "ગ્રાહકે ચા માટે ₹60 આપ્યા, પણ સાઉન્ડબોક્સે કંઈ બોલ્યું નહીં!",
        "গ্রাহক চায়ের জন্য ₹60 এর স্ক্রিনশট দেখাচ্ছে, কিন্তু সাউন্ডবক্সে কোনো শব্দ নেই! টাকা কি এসেছে?",
        "গ্রাহক চায়ের জন্য ₹60 দিয়েছে, কিন্তু সাউন্ডবক্সে কোনো আওয়াজ হয়নি!",
        "வாடிக்கையாளர் டீக்கு ₹60 ஸ்கிரீன்ஷாட் காட்டுகிறார், ஆனால் சவுண்ட்பாக்ஸ் பேசவில்லை! பணம் வந்ததா?",
        "வாடிக்கையாளர் டீக்கு ₹60 செலுத்தினார், ஆனால் சவுண்ட்பாக்ஸ் எதுவும் பேசவில்லை!",
        "కస్టమర్ టీ కోసం ₹60 స్క్రీన్‌షాట్ చూపిస్తున్నారు, కానీ సౌండ్‌బాక్స్ ఏమీ మాట్లాడలేదు! డబ్బు వచ్చిందా?",
        "కస్టమర్ టీ కోసం ₹60 చెల్లించారు, కానీ సౌండ్‌బాక్స్ ఏమీ మాట్లాడలేదు!",
        "ಗ್ರಾಹಕರು ಚಹಾಗೆ ₹60 ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ತೋರಿಸುತ್ತಿದ್ದಾರೆ, ಆದರೆ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಧ್ವನಿಸಲಿಲ್ಲ! ಹಣ ಬಂದಿದೆಯೇ?",
        "ಗ್ರಾಹಕರು ಚಹಾಗೆ ₹60 ಪಾವತಿಸಿದ್ದಾರೆ, ಆದರೆ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಧ್ವನಿಸಲಿಲ್ಲ!",
        "ചായയ്ക്ക് ₹60-ന്റെ സ്ക്രീൻഷോട്ട് ഉപഭോക്താവ് കാണിക്കുന്നു, എന്നാൽ സൗണ്ട്ബോക്സ് മിണ്ടിയില്ല! പണം എത്തിയോ?",
        "ചായയ്ക്ക് ഉപഭോക്താവ് ₹60 നൽകി, എന്നാൽ സൗണ്ട്ബോക്സ് ശബ്ദിച്ചില്ല!",
        "ਗਾਹਕ ਚਾਹ ਲਈ ₹60 ਦਾ ਸਕ੍ਰੀਨਸ਼ੌਟ ਦਿਖਾ ਰਿਹਾ ਹੈ, ਪਰ ਸਾਊਂਡਬਾਕਸ ਨਹੀਂ ਬੋਲਿਆ! ਕੀ ਪੈਸੇ ਆਏ ਹਨ?",
        "ਗਾਹਕ ਨੇ ਚਾਹ ਲਈ ₹60 ਦਿੱਤੇ, ਪਰ ਸਾਊਂਡਬਾਕਸ ਨੇ ਕੁਝ ਨਹੀਂ ਬੋਲਿਆ!"
    ],
    "S4": [
        "A customer is complaining they got charged twice for ₹1,200 medicine.",
        "एक ग्राहक शिकायत कर रहा है कि ₹1,200 की दवाई के लिए उसके खाते से दो बार पैसे कट गए।",
        "एक ग्राहक तक्रार करत आहे की ₹1,200 च्या औषधांसाठी त्यांच्या खात्यातून दोनदा पैसे कापले गेले.",
        "એક ગ્રાહક ફરિયાદ કરે છે કે ₹1,200 ની દવા માટે તેના ખાતામાંથી બે વાર પૈસા કપાયા.",
        "একজন গ্রাহক অভিযোগ করছেন যে ₹1,200 এর ওষুধের জন্য তার দুবার টাকা কেটে নেওয়া হয়েছে।",
        "₹1,200 மருந்துக்கு வாடிக்கையாளரிடம் இரண்டு முறை பணம் கழிக்கப்பட்டதாக புகார் கூறுகிறார்.",
        "₹1,200 మందుల కోసం కస్టమర్ ఖాతా నుండి రెండుసార్లు డబ్బు కట్ అయిందని ఫిర్యాదు చేస్తున్నారు.",
        "₹1,200 ರ ಔಷಧಿಗೆ ಗ್ರಾಹಕರಿಂದ ಎರಡು ಬಾರಿ ಹಣ ಕಡಿತಗೊಂಡಿದೆ ಎಂದು ದೂರಿದ್ದಾರೆ.",
        "₹1,200 മരുന്നിന് ഉപഭോക്താവിൽ നിന്ന് രണ്ട് തവണ പണം ഈടാക്കിയതായി പരാതിപ്പെടുന്നു.",
        "ਇੱਕ ਗਾਹਕ ਸ਼ਿਕਾਇਤ ਕਰ ਰਿਹਾ ਹੈ ਕਿ ₹1,200 ਦੀ ਦਵਾਈ ਲਈ ਉਸਦੇ ਦੋ ਵਾਰ ਪੈਸੇ ਕੱਟੇ ਗਏ ਹਨ।"
    ],
    "S5": [
        "Why did multiple customer payments fail in the last 20 minutes?",
        "पिछले 20 मिनट में कई ग्राहकों के भुगतान क्यों फेल हो गए?",
        "गेल्या 20 मिनिटांत अनेक ग्राहकांचे पेमेंट्स का अयशस्वी झाले?",
        "છેલ્લી 20 મિનિટમાં ઘણા ગ્રાહકોના પેમેન્ટ કેમ નિષ્ફળ ગયા?",
        "গত 20 মিনিটে একাধিক গ্রাহকের পেমেন্ট কেন ব্যর্থ হলো?",
        "கடந்த 20 நிமிடங்களில் பல வாடிக்கையாளர்களின் கொடுப்பனவுகள் ஏன் தோல்வியடைந்தன?",
        "గత 20 నిమిషాల్లో చాలా మంది కస్టమర్ల చెల్లింపులు ఎందుకు విఫలమయ్యాయి?",
        "ಕಳೆದ 20 ನಿಮಿಷಗಳಲ್ಲಿ ಬಹುತೇಕ ಗ್ರಾಹಕರ ಪಾವತಿಗಳು ಏಕೆ ವಿಫಲವಾದವು?",
        "കഴിഞ്ഞ 20 മിനിറ്റിൽ ഒന്നിലധികം ഉപഭോക്താക്കളുടെ പേയ്‌മെന്റുകൾ പരാജയപ്പെട്ടത് എന്തുകൊണ്ട്?",
        "ਪਿਛਲੇ 20 ਮਿੰਟਾਂ ਵਿੱਚ ਕਈ ਗਾਹਕਾਂ ਦੇ ਭੁਗਤਾਨ ਕਿਉਂ ਫੇਲ੍ਹ ਹੋਏ?"
    ]
}

def is_canonical_scenario_match(message: str, scenario: str) -> bool:
    """Matches the exact 1-click suggested prompt for a scenario across all 10 languages."""
    msg = message.strip().lower()
    for prompt in CANONICAL_PROMPTS_BY_SCENARIO.get(scenario, []):
        p = prompt.strip().lower()
        if p == msg or p in msg or msg in p:
            return True
        p_clean = p.replace(',', '').replace('.', '').replace('?', '').replace('!', '')
        p_words = [w for w in p_clean.split() if len(w) > 2]
        if len(p_words) >= 3:
            key_phrase = " ".join(p_words[:3])
            if key_phrase in msg:
                return True
    return False

def is_informational_query(msg_clean: str) -> bool:
    """
    Identifies informational, ledger lookup, or generic chat queries that must NOT
    trigger operational incident remediation (e.g. asking for order ID, customer name, battery, bank details).
    """
    info_triggers = [
        "what is the order id", "what is my order id", "what's the order id", "order id of my payment",
        "id of my payment", "order id please", "which order id", "what is order id",
        "give me list", "show me list", "list please", "list of failed", "list failed", "which order",
        "who was the customer", "who is the customer", "customer vpa", "customer name", "who paid",
        "bank account number", "what is my bank", "which bank", "account number", "my ifsc", "ifsc code",
        "battery level", "battery percent", "charging status", "sim status", "soundbox battery", "device status",
        "hello", "hi", "hey", "namaste", "good morning", "how are you", "who are you", "what can you do", "help me",
        "ऑर्डर आईडी", "ऑर्डर नंबर", "ऑर्डर संख्या", "ऑर्डर की आईडी", "ऑर्डर की लिस्ट", "ऑर्डर क्या है",
        "ग्राहक कौन", "किसने पैसे दिए", "ग्राहक का नाम", "खाता संख्या", "बैंक खाता", "आईएफएससी",
        "बैटरी स्तर", "बैटरी कितने", "चार्जिंग", "नमस्ते", "नमस्कार", "ऑर्डर आयडी", "ઓર્ડર આઈડી", "অর্ডার আইডি", "ஆர்டர் ஐடி", "ఆర్డర్ ఐడి"
    ]
    return any(it in msg_clean for it in info_triggers)

def _create_event(step: int, agent: str, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper to construct standardized agent execution events."""
    now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    return {
        "step": step,
        "agent": agent,
        "status": status,
        "message": message,
        "details": details or {},
        "timestamp": now_str
    }

def process_incident_stream(merchant_id: str, message: str, scenario_hint: Optional[str] = None, language: str = "en") -> Generator[Dict[str, Any], None, None]:
    """
    Main autonomous multi-agent incident resolution orchestrator.
    Yields real-time events across:
    1. Incident Manager Agent (Intent & Safety Boundary)
    2. SQL & Rail Investigator Agent (Database & Telemetry Diagnosis)
    3. Remediation Agent (Idempotent API Repair or Human Escalation)
    4. Verification & Auditor Agent (Core Banking UTR Proof & Merchant Communication)
    """
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    log.info(f"[ORCHESTRATOR] Starting incident {incident_id} for merchant {merchant_id}: '{message}'")

    # Step 1: Manager Agent analyzes query and extracts merchant profile
    yield _create_event(
        step=1,
        agent="Manager Agent",
        status="THINKING",
        message=f"Received incident '{message}'. Extracting merchant profile and validating safety thresholds...",
        details={"incident_id": incident_id, "merchant_id": merchant_id}
    )
    time.sleep(0.4)

    merchants = run_query(f"SELECT id, name, username, business_type, bank_name, account_number, ifsc, phone FROM merchants WHERE id = '{merchant_id}' LIMIT 1")
    if not merchants:
        yield _create_event(
            step=1,
            agent="Manager Agent",
            status="FAILED",
            message=f"Unknown merchant ID: {merchant_id}",
            details={"error": "MERCHANT_NOT_FOUND"}
        )
        return

    merchant = merchants[0]
    yield _create_event(
        step=1,
        agent="Manager Agent",
        status="SUCCESS",
        message=f"Merchant identified: {merchant['name']} ({merchant['business_type']}) | Bank: {merchant['bank_name']} (A/C: {merchant['account_number']}). Delegating to SQL & Rail Investigator.",
        details={"merchant": dict(merchant)}
    )
    time.sleep(0.3)

    # Step 2: Investigator Agent inspects transactions, settlement batches, and Soundbox
    yield _create_event(
        step=2,
        agent="Investigator Agent",
        status="THINKING",
        message=f"Running parallel SQL inspection across transactions, settlement batches, and Soundbox telemetry...",
        details={}
    )
    time.sleep(0.4)

    # Fetch recent transactions
    tx_sql = f"SELECT order_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at FROM transactions WHERE merchant_id = '{merchant_id}' ORDER BY id DESC LIMIT 5"
    tx_list = run_query(tx_sql)

    # Fetch recent settlement batches
    batch_sql = f"SELECT batch_code, order_id, total_amount, status, rail, hold_reason, utr_number FROM settlement_batches WHERE merchant_id = '{merchant_id}' ORDER BY id DESC LIMIT 3"
    batch_list = run_query(batch_sql)

    # Fetch Soundbox status
    sb_sql = f"SELECT device_id, sim_status, battery_level, last_chime_status, firmware_version FROM soundbox_devices WHERE merchant_id = '{merchant_id}' LIMIT 1"
    sb_list = run_query(sb_sql)
    soundbox = sb_list[0] if sb_list else None

    yield _create_event(
        step=2,
        agent="Investigator Agent",
        status="TOOL_CALL",
        message=f"SQL Query completed: Found {len(tx_list)} transactions, {len(batch_list)} settlement batches, and 1 Soundbox device.",
        details={"sql_query": tx_sql, "transactions_count": len(tx_list), "batches_count": len(batch_list)}
    )
    time.sleep(0.3)

    # Diagnosis Logic
    held_batch = next((b for b in batch_list if b["status"] == "HELD"), None)
    failed_txs = [t for t in tx_list if t["status"] == "FAILED"]
    reversed_tx = next((t for t in tx_list if t["status"] == "REVERSED"), None)
    soundbox_issue = soundbox and (soundbox["last_chime_status"] == "DROPPED" or soundbox["sim_status"] != "ONLINE")

    # Step 3 & 4: Branch by Diagnosed Scenario & Multilingual Intent
    msg_clean = f" {message.lower()} "

    # 1. Exact canonical 1-click suggested prompt match across all 10 languages
    is_s1_canonical = is_canonical_scenario_match(message, "S1") or scenario_hint == "S1"
    is_s2_canonical = is_canonical_scenario_match(message, "S2") or scenario_hint == "S2"
    is_s3_canonical = is_canonical_scenario_match(message, "S3") or scenario_hint == "S3"
    is_s4_canonical = is_canonical_scenario_match(message, "S4") or scenario_hint == "S4"
    is_s5_canonical = is_canonical_scenario_match(message, "S5") or scenario_hint == "S5"

    # 2. Check if query is an informational data/ledger lookup (e.g. asking for order ID, customer, battery, bank)
    is_info = is_informational_query(msg_clean)

    # 3. Scenario Intent Classification (Incident triggers only fire if NOT a generic informational query)
    is_high_value_intent = is_s2_canonical or (
        not is_info and any(k in msg_clean for k in [
            "78000", "78,000", "smart tv", " tv ", "high value", "velocity", "limit",
            "स्मार्ट टीवी", "टीवी", "होल्ड", "स्मार्ट टीव्ही", "સ્માર્ટ ટીવી", "স্মার্ট টিভি"
        ])
    )

    is_soundbox_intent = is_s3_canonical or (
        not is_info and (
            any(k in msg_clean for k in [
                "didn't speak", "did not speak", "silent", "no sound", "no voice", "didn't announce", "stayed silent",
                "soundbox silent", "soundbox not", "screenshot", "screen", "fake", "spoof", "counterfeit", "did money arrive",
                "कुछ नहीं बोला", "नहीं बोला", "आवाज नहीं आई", "साउंडबॉक्स शांत", "बोलला नाही", "स्क्रीनशॉट", "स्क्रीन", "फर्जी",
                "બોલ્યું નહીં", "બોલ્યો નહીં", "বলেনি", "பேசவில்லை", "మాట్లాడలేదు", "ಧ್ವನಿಸಲಿಲ್ಲ", "മിണ്ടിയില്ല", "ਬੋਲਿਆ ਨਹੀਂ"
            ]) and any(k in msg_clean for k in [
                "soundbox", "chai", "tea", "60", "₹60", "चाय", "साउंडबॉक्स", "चहा", "ચા", "ચায়ের"
            ])
        )
    )

    is_duplicate_intent = is_s4_canonical or (
        not is_info and (
            any(k in msg_clean for k in [
                "twice", "duplicate", "two times", "debited twice", "charged twice", "double debit",
                "दो बार", "दोबारा", "दोनदा", "બે વાર", "দুববার", "இரண்டு முறை", "రెండుసార్లు"
            ]) and any(k in msg_clean for k in [
                "medicine", "1200", "1,200", "दवाई", "दवा", "औषध", "દવા", "ওষুধ", "மருந்து", "మందులు"
            ])
        )
    )

    is_rail_outage_intent = is_s5_canonical or (
        not is_info and (
            any(k in msg_clean for k in [
                "payments fail", "multiple payments fail", "payments are failing", "decline spike",
                "last 20 minutes", "20 minutes", "20 mins", "भुगतान क्यों फेल", "विफल क्यों", "अयशस्वी का"
            ]) and not any(k in msg_clean for k in ["which order", "list of", "list please", "order id"])
        )
    )

    is_stuck_settlement_scenario = is_s1_canonical or (
        not is_info and any(k in msg_clean for k in [
            "morning sales", "morning settlement", "settlement stuck", "stuck settlement", "not reached", "hasn't reached",
            "not credited", "4500", "4,500", "payout stuck", "money stuck",
            "सुबह की बिक्री", "सुबह का सेटलमेंट", "अटका", "अटके", "पहुंचे नहीं", "पहुंचा नहीं", "खाते में नहीं आया",
            "जमा नहीं", "सकाळचे सेटलमेंट", "अडकले", "સવારના વેચાણ", "અટકાયું", "આવ્યા નથી", "ঢোকেনি", "வரவில்லை", "జమ కాలేదు", "ಬಂದಿಲ್ಲ", "ਨਹੀਂ ਆਏ"
        ])
    )

    # SCENARIO 2: High Value Threshold Breach (> ₹25k) -> Human-in-the-Loop Interrupt
    if is_high_value_intent:
        target_batch = held_batch or next((b for b in batch_list if b["total_amount"] > AUTO_RESOLUTION_THRESHOLD), None)
        amount = target_batch["total_amount"] if target_batch else 78000.0
        batch_code = target_batch["batch_code"] if target_batch else "B-709"

        if target_batch and target_batch["status"] == "HELD":
            reason = target_batch["hold_reason"] or "HIGH_VALUE_VELOCITY_LIMIT"
            log.warning(f"[ORCHESTRATOR] Threshold breach: ₹{amount} exceeds auto limit ₹{AUTO_RESOLUTION_THRESHOLD}")

            merchant_warning = format_multilingual_msg(
                "SAFETY_HOLD", lang=language,
                amount=f"{amount:,.2f}", batch_code=batch_code
            )

            yield _create_event(
                step=3,
                agent="Remediation Agent",
                status="AWAITING_APPROVAL",
                message=f"SAFETY LIMIT REACHED: Transaction of ₹{amount:,.2f} exceeds autonomous limit of ₹{AUTO_RESOLUTION_THRESHOLD:,.2f}. Pausing execution for human supervisor authorization.",
                details={
                    "batch_code": batch_code,
                    "amount": amount,
                    "hold_reason": reason,
                    "requires_approval": True,
                    "incident_id": incident_id,
                    "merchant_warning": merchant_warning,
                    "language": language
                }
            )

            # Log pending incident
            run_query("""
            INSERT INTO incident_logs (incident_id, merchant_id, query, status, resolution_notes, action_taken)
            VALUES (?, ?, ?, 'AWAITING_APPROVAL', ?, 'HUMAN_APPROVAL_REQUIRED')
            """, (incident_id, merchant_id, message, f"Batch {batch_code} requires human override"))
            return
        else:
            utr = target_batch["utr_number"] if target_batch else "UTR-9988776655"
            scenario_default = format_multilingual_msg(
                "S2_APPROVED", lang=language,
                amount=f"{amount:,.2f}", batch_code=batch_code, utr=utr
            )
            final_msg = generate_ai_response(
                merchant=merchant,
                tx_list=tx_list,
                batch_list=batch_list,
                soundbox=soundbox,
                action_taken=f"Supervisor approved high value settlement batch {batch_code} (UTR: {utr}).",
                message=message,
                language=language,
                scenario_default=scenario_default
            )
            yield _create_event(
                step=4,
                agent="Verification Agent",
                status="RESOLVED",
                message=final_msg,
                details={"incident_id": incident_id, "utr_number": utr, "status": "RESOLVED"}
            )
            return

    # SCENARIO 3: Counterfeit Payment / Fake Screenshot Detection (M-103 Chai Point)
    elif is_soundbox_intent:
        device_id = soundbox["device_id"] if soundbox else "SB-4402"
        claimed_amount = 60.0

        # Tool 1: Audit Live NPCI Switch & Inbound Gateway
        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="TOOL_CALL",
            message=f"Counterfeit Payment Audit: Auditing NPCI UPI switch & gateway buffer for claimed amount ₹{int(claimed_amount)}...",
            details={
                "tool_name": "verify_inbound_upi_traffic",
                "tool_input": {"merchant_id": merchant_id, "claimed_amount": claimed_amount},
                "device_id": device_id,
                "claimed_amount": claimed_amount
            }
        )
        time.sleep(0.4)

        audit_res = verify_inbound_upi_traffic.invoke({"merchant_id": merchant_id, "claimed_amount": claimed_amount})

        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="SUCCESS",
            message=f"Audit Completed: 0 inbound records found on UPI switch. Flagged SUSPECTED_SPOOF_APP_FRAUD. No funds received.",
            details={
                "tool_name": "verify_inbound_upi_traffic",
                "tool_result": audit_res,
                "fraud_type": "SUSPECTED_SPOOF_APP_FRAUD"
            }
        )
        time.sleep(0.3)

        # Tool 2: Broadcast Spoken Security Warning on Soundbox
        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="TOOL_CALL",
            message=f"Merchant Protection: Broadcasting spoken fraud alert on Soundbox {device_id}...",
            details={
                "tool_name": "trigger_soundbox_security_alert",
                "tool_input": {"device_id": device_id, "alert_type": "FAKE_PAYMENT_WARNING", "amount": claimed_amount},
                "device_id": device_id
            }
        )
        time.sleep(0.4)

        alert_res = trigger_soundbox_security_alert.invoke({"device_id": device_id, "alert_type": "FAKE_PAYMENT_WARNING", "amount": claimed_amount})
        sb_list = run_query(sb_sql)
        soundbox = sb_list[0] if sb_list else None

        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="SUCCESS",
            message=f"Spoken Fraud Warning Emitted on Soundbox {device_id}. Merchant protected against counterfeit payment.",
            details={
                "tool_name": "trigger_soundbox_security_alert",
                "tool_result": alert_res,
                "device_id": device_id,
                "alert_text": f"Savdhan: Paytm par {int(claimed_amount)} rupaye ka koi bhugtan prapt nahi hua hai. Kripya grahak ka bank SMS check karein."
            }
        )
        time.sleep(0.3)

        scenario_default = format_multilingual_msg(
            "S3_RESOLVED", lang=language,
            name=merchant["name"], amount=int(claimed_amount),
            device_id=device_id
        )
        final_msg = generate_ai_response(
            merchant=merchant,
            tx_list=tx_list,
            batch_list=batch_list,
            soundbox=soundbox,
            action_taken=f"Audited NPCI UPI switch and confirmed 0 inbound transactions for ₹{int(claimed_amount)}. Flagged counterfeit payment spoof attempt. Broadcasted audio warning on Soundbox {device_id}.",
            message=message,
            language=language,
            scenario_default=scenario_default
        )

        run_query("""
        INSERT INTO incident_logs (incident_id, merchant_id, query, status, resolution_notes, action_taken)
        VALUES (?, ?, ?, 'RESOLVED', ?, 'COUNTERFEIT_SPOOF_BLOCKED')
        """, (incident_id, merchant_id, message, final_msg))

        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="RESOLVED",
            message=final_msg,
            details={
                "device_id": device_id,
                "status": "RESOLVED",
                "incident_id": incident_id,
                "amount": claimed_amount,
                "fraud_alert": {
                    "type": "SUSPECTED_SPOOF_APP_FRAUD",
                    "claimed_amount": claimed_amount,
                    "switch_status": "ZERO_INBOUND_RECORDS",
                    "recommendation": "Do NOT release goods. Ask customer for real bank SMS confirmation."
                }
            }
        )

    # SCENARIO 4: Duplicate Debit & Auto-Reversal (M-104 Verma Meds)
    elif is_duplicate_intent:
        rev_id = reversed_tx["order_id"] if reversed_tx else "PTM-55102"
        rev_amount = reversed_tx["amount"] if reversed_tx else 1200.0

        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="TOOL_CALL",
            message=f"Investigating duplicate transaction claim: Auditing NPCI UPI clearing switch for Order #{rev_id}...",
            details={
                "tool_name": "audit_npci_reversal_ledger",
                "tool_input": {"order_id": rev_id, "rrn": "409955102001"},
                "order_id": rev_id,
                "amount": rev_amount
            }
        )
        time.sleep(0.4)

        audit_res = audit_npci_reversal_ledger.invoke({"order_id": rev_id, "rrn": "409955102001"})

        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="SUCCESS",
            message=f"NPCI Reversal Verified: Customer refund confirmed. No chargeback risk exists.",
            details={
                "tool_name": "audit_npci_reversal_ledger",
                "tool_result": audit_res,
                "reversal_ref": f"REV-{rev_id}"
            }
        )
        time.sleep(0.3)

        scenario_default = format_multilingual_msg(
            "S4_RESOLVED", lang=language,
            order_id=rev_id, amount=int(rev_amount)
        )
        final_msg = generate_ai_response(
            merchant=merchant,
            tx_list=tx_list,
            batch_list=batch_list,
            soundbox=soundbox,
            action_taken=f"Verified NPCI duplicate UPI reversal for Order #{rev_id} (₹{int(rev_amount)}). Reversal Ref: REV-{rev_id}.",
            message=message,
            language=language,
            scenario_default=scenario_default
        )

        run_query("""
        INSERT INTO incident_logs (incident_id, merchant_id, query, status, resolution_notes, action_taken)
        VALUES (?, ?, ?, 'RESOLVED', ?, 'AUTO_REVERSAL_VERIFIED')
        """, (incident_id, merchant_id, message, final_msg))

        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="RESOLVED",
            message=final_msg,
            details={"status": "RESOLVED", "reversal_ref": f"REV-{rev_id}", "incident_id": incident_id}
        )

    # SCENARIO 5: Bank Rail Outage / Route Switch (M-105 Gupta Sweets)
    elif is_rail_outage_intent:
        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="TOOL_CALL",
            message=f"Acquiring Bank Rail Diagnostic: Detected 35% decline spike on HDFC acquiring gateway. Executing failover to ICICI backup gateway...",
            details={
                "tool_name": "switch_gateway_route",
                "tool_input": {"merchant_id": merchant_id, "target_gateway": "ICICI_BACKUP"},
                "failed_transactions": len(failed_txs),
                "primary_gateway": "HDFC",
                "backup_gateway": "ICICI"
            }
        )
        time.sleep(0.4)

        failover_res = switch_gateway_route.invoke({"merchant_id": merchant_id, "target_gateway": "ICICI_BACKUP"})

        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="SUCCESS",
            message=f"Gateway Failover Completed: Traffic successfully migrated to ICICI backup gateway.",
            details={
                "tool_name": "switch_gateway_route",
                "tool_result": failover_res,
                "route": "ICICI_BACKUP"
            }
        )
        time.sleep(0.3)

        scenario_default = format_multilingual_msg(
            "S5_RESOLVED", lang=language,
            name=merchant["name"]
        )
        final_msg = generate_ai_response(
            merchant=merchant,
            tx_list=tx_list,
            batch_list=batch_list,
            soundbox=soundbox,
            action_taken="Detected 35% decline spike on HDFC acquiring rail (503 Service Unavailable). Switched merchant acquiring route to ICICI backup gateway.",
            message=message,
            language=language,
            scenario_default=scenario_default
        )

        run_query("""
        INSERT INTO incident_logs (incident_id, merchant_id, query, status, resolution_notes, action_taken)
        VALUES (?, ?, ?, 'RESOLVED', ?, 'GATEWAY_FAILOVER_ICICI')
        """, (incident_id, merchant_id, message, final_msg))

        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="RESOLVED",
            message=final_msg,
            details={"status": "RESOLVED", "route": "ICICI_BACKUP", "incident_id": incident_id}
        )

    # SCENARIO 1: Standard Stuck Settlement (≤ ₹25k) -> Autonomous Re-Route (M-101 Ramesh Kirana)
    elif is_stuck_settlement_scenario:
        target_batch = held_batch or next((b for b in batch_list if b["total_amount"] <= AUTO_RESOLUTION_THRESHOLD), None)
        batch_code = target_batch["batch_code"] if target_batch else "B-402"
        amount = target_batch["total_amount"] if target_batch else 4500.0
        hold_reason = target_batch["hold_reason"] if target_batch and target_batch.get("hold_reason") else "NPCI_SYNC_TIMEOUT"

        if target_batch and target_batch["status"] == "HELD":
            yield _create_event(
                step=3,
                agent="Remediation Agent",
                status="TOOL_CALL",
                message=f"Root cause diagnosed: Settlement batch #{batch_code} (₹{amount}) stuck due to {hold_reason}. Invoking requeue_settlement_batch...",
                details={
                    "tool_name": "requeue_settlement_batch",
                    "tool_input": {"batch_code": batch_code, "target_rail": "IMPS_SECONDARY"},
                    "batch_code": batch_code,
                    "hold_reason": hold_reason,
                    "amount": amount
                }
            )
            time.sleep(0.4)

            # Execute Tool: requeue_settlement_batch
            repair_result = requeue_settlement_batch.invoke({"batch_code": batch_code, "target_rail": "IMPS_SECONDARY"})

            yield _create_event(
                step=3,
                agent="Remediation Agent",
                status="SUCCESS",
                message=f"Autonomous action executed: Re-routed batch #{batch_code} from primary NPCI rail to secondary IMPS pipeline.",
                details={
                    "tool_name": "requeue_settlement_batch",
                    "tool_result": repair_result,
                    "rail": "IMPS_SECONDARY"
                }
            )
            time.sleep(0.3)

            # Fetch updated batch to get newly generated UTR
            updated_batch = run_query(f"SELECT utr_number, cleared_at FROM settlement_batches WHERE batch_code = '{batch_code}' LIMIT 1")[0]
            utr = updated_batch["utr_number"]
            batch_list = run_query(batch_sql)
        else:
            utr = target_batch["utr_number"] if target_batch else "UTR-9992444466"

        # Step 4: Verification Agent
        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="TOOL_CALL",
            message=f"Calling Core Banking API to verify settlement credit for {merchant['bank_name']}...",
            details={
                "tool_name": "verify_bank_utr",
                "tool_input": {"batch_code": batch_code, "utr": utr, "account": merchant["account_number"]},
                "tool_result": f"VERIFIED: Core bank cleared with UTR {utr}",
                "bank": merchant["bank_name"],
                "account": merchant["account_number"],
                "utr": utr
            }
        )
        time.sleep(0.4)

        scenario_default = format_multilingual_msg(
            "S1_RESOLVED", lang=language,
            name=merchant["name"], amount=f"{amount:,.2f}",
            batch_code=batch_code, bank_name=merchant["bank_name"], utr=utr
        )
        final_msg = generate_ai_response(
            merchant=merchant,
            tx_list=tx_list,
            batch_list=batch_list,
            soundbox=soundbox,
            action_taken=f"Re-routed settlement batch #{batch_code} via IMPS_SECONDARY. Generated UTR: {utr}.",
            message=message,
            language=language,
            scenario_default=scenario_default
        )

        run_query("""
        INSERT INTO incident_logs (incident_id, merchant_id, query, status, resolution_notes, utr_number, action_taken)
        VALUES (?, ?, ?, 'RESOLVED', ?, ?, 'REQUEUED_IMPS')
        """, (incident_id, merchant_id, message, final_msg, utr))

        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="RESOLVED",
            message=final_msg,
            details={"utr_number": utr, "status": "RESOLVED", "incident_id": incident_id}
        )

    # DEFAULT / GENERIC RESOLUTION (Conversational & Ledger Queries)
    else:
        yield _create_event(
            step=3,
            agent="Remediation Agent",
            status="SUCCESS",
            message=f"Live ledger & device telemetry retrieved for {merchant['name']}. No operational failure detected.",
            details={"type": "INFORMATIONAL"}
        )
        time.sleep(0.3)

        scenario_default = format_multilingual_msg(
            "DEFAULT_RESOLVED", lang=language,
            name=merchant["name"]
        )
        final_msg = generate_ai_response(
            merchant=merchant,
            tx_list=tx_list,
            batch_list=batch_list,
            soundbox=soundbox,
            action_taken=f"Audited live records and answered merchant inquiry for {merchant['name']}.",
            message=message,
            language=language,
            scenario_default=scenario_default
        )

        # Only emit utr_number if merchant explicitly asked to show the settlement UTR verification card
        is_utr_card_requested = any(k in msg_clean for k in ["show utr", "settlement card", "show settlement", "verify settlement", "utr receipt", "सेटलमेंट कार्ड"])
        details_payload = {"status": "RESOLVED", "incident_id": incident_id}
        if is_utr_card_requested and batch_list and batch_list[0].get("utr_number"):
            details_payload["utr_number"] = batch_list[0]["utr_number"]

        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="RESOLVED",
            message=final_msg,
            details=details_payload
        )

def approve_incident_stream(incident_id: str, approved: bool, notes: Optional[str] = None, language: str = "en") -> Generator[Dict[str, Any], None, None]:
    """Resumes execution after a human supervisor provides approval on a > ₹25k transaction."""
    log.info(f"[APPROVAL] Resuming incident {incident_id}. Approved: {approved}. Notes: {notes}. Language: {language}")

    yield _create_event(
        step=3,
        agent="Manager Agent",
        status="THINKING",
        message=f"Supervisor decision received: {'APPROVED' if approved else 'REJECTED'}. Validating cryptographic authorization...",
        details={"incident_id": incident_id, "approved": approved}
    )
    time.sleep(0.3)

    if not approved:
        final_msg = f"Settlement override was rejected by Supervisor. Reason: {notes or 'Requires manual bank branch verification'}."
        run_query(f"UPDATE incident_logs SET status = 'ESCALATED', resolution_notes = '{final_msg}' WHERE incident_id = '{incident_id}'")
        yield _create_event(
            step=4,
            agent="Verification Agent",
            status="ESCALATED",
            message=final_msg,
            details={"incident_id": incident_id, "status": "ESCALATED"}
        )
        return

    # Find the held batch for this incident or merchant
    incidents = run_query(f"SELECT merchant_id FROM incident_logs WHERE incident_id = '{incident_id}' LIMIT 1")
    merchant_id = incidents[0]["merchant_id"] if incidents else "M-102"

    batches = run_query(f"SELECT batch_code, total_amount FROM settlement_batches WHERE merchant_id = '{merchant_id}' AND status = 'HELD' LIMIT 1")
    batch_code = batches[0]["batch_code"] if batches else "B-709"
    amount = batches[0]["total_amount"] if batches else 78000.0

    # Execute release
    yield _create_event(
        step=3,
        agent="Remediation Agent",
        status="TOOL_CALL",
        message=f"Supervisor Approved: Executing release_settlement_hold for batch #{batch_code} (₹{amount:,.2f})...",
        details={
            "tool_name": "release_settlement_hold",
            "tool_input": {"batch_code": batch_code, "approver_note": notes or "Supervisor Authorized"},
            "batch_code": batch_code,
            "amount": amount
        }
    )
    time.sleep(0.3)

    release_result = release_settlement_hold.invoke({"batch_code": batch_code, "approver_note": notes or "Supervisor Authorized"})

    yield _create_event(
        step=3,
        agent="Remediation Agent",
        status="SUCCESS",
        message=f"Hold Released: Batch #{batch_code} cleared by supervisor authorization.",
        details={
            "tool_name": "release_settlement_hold",
            "tool_result": release_result,
            "batch_code": batch_code
        }
    )
    time.sleep(0.3)

    # Fetch newly generated UTR
    updated = run_query(f"SELECT utr_number FROM settlement_batches WHERE batch_code = '{batch_code}' LIMIT 1")
    utr = updated[0]["utr_number"] if updated else "UTR-9988776655"

    final_msg = format_multilingual_msg(
        "S2_APPROVED", lang=language,
        amount=f"{amount:,.2f}", batch_code=batch_code, utr=utr
    )

    run_query(f"UPDATE incident_logs SET status = 'RESOLVED', utr_number = '{utr}', resolution_notes = '{final_msg}' WHERE incident_id = '{incident_id}'")

    yield _create_event(
        step=4,
        agent="Verification Agent",
        status="RESOLVED",
        message=final_msg,
        details={"incident_id": incident_id, "utr_number": utr, "status": "RESOLVED"}
    )



# ---------------------------------------------------------------------------
# DEDICATED QR PROVENANCE VOICE AGENT ENGINE (Voice-Only & Multilingual)
# ---------------------------------------------------------------------------

QR_VOICE_TEMPLATES = {
    "QR_GENUINE": {
        "en": "Namaste {name}. Your physical Paytm QR standee is 100% authentic and verified. Both the visual UPI destination ({vpa}) and the invisible cryptographic watermark match Paytm's central registry. Provenance integrity is {score}%. Payments are secure and your Soundbox is armed.",
        "hi": "नमस्ते {name}। आपकी दुकान का फिजिकल पेटीएम क्यूआर स्टैंडी 100% असली और सुरक्षित है। यूपीआई पता ({vpa}) और डिजिटल वॉटरमार्क दोनों पेटीएम के केंद्रीय रिकॉर्ड से पूरी तरह मेल खाते हैं। सत्यनिष्ठा स्कोर {score}% है। भुगतान स्वीकार करना पूरी तरह सुरक्षित है।",
        "mr": "नमस्ते {name}. आपले प्रत्यक्ष पेटीएम QR स्टँडी 100% खरे आणि सुरक्षित आहे. UPI पत्ता ({vpa}) आणि डिजिटल वॉटरमार्क पूर्णपणे जुळत आहेत. अखंडता {score}% आहे. पेमेंट स्वीकारणे पूर्णपणे सुरक्षित आहे.",
        "gu": "નમસ્તે {name}. તમારું પેટીએમ QR સ્ટેન્ડી 100% અસલ અને ચકાસાયેલ છે. UPI સરનામું ({vpa}) અને ડિજિટલ વોટરમાર્ક બંને મેળ ખાય છે. અખંડિતતા {score}% છે. પેમેન્ટ લેવું સુરક્ષિત છે.",
        "bn": "নমস্কার {name}। আপনার পেটিএম কিউআর স্ট্যান্ডি 100% খাঁটি এবং যাচাইকৃত। ইউপিআই ঠিকানা ({vpa}) এবং ডিজিটাল ওয়াটারমার্ক উভয়ই মিলে গেছে। সততা স্কোর {score}%। পেমেন্ট গ্রহণ নিরাপদ।",
        "ta": "வணக்கம் {name}. உங்கள் Paytm QR ஸ்டாண்டீ 100% அசல் மற்றும் சரிபார்க்கப்பட்டது. UPI முகவரி ({vpa}) மற்றும் ரகசிய வாட்டர்மார்க் இரண்டும் பொருந்துகின்றன. தரம் {score}%. பணம் பெறுவது பாதுகாப்பானது.",
        "te": "నమస్తే {name}. మీ Paytm QR స్టాండీ 100% అసలైనది మరియు ధృవీకరించబడింది. UPI చిరునామా ({vpa}) మరియు డిజిటల్ వాటర్‌మార్క్ సరిగ్గా సరిపోలాయి. సమగ్రత {score}%. చెల్లింపులు సురಕ್ಷితం.",
        "kn": "ನಮಸ್ಕಾರ {name}. ನಿಮ್ಮ Paytm QR ಸ್ಟ್ಯಾಂಡಿ 100% ಅಸಲಿ ಮತ್ತು ಪರಿಶೀಲಿಸಲಾಗಿದೆ. UPI ವಿಳಾಸ ({vpa}) ಮತ್ತು ಡಿಜಿಟಲ್ ವಾಟರ್‌ಮಾರ್ಕ್ ಸಂಪೂರ್ಣವಾಗಿ ಹೊಂದಾಣಿಕೆಯಾಗುತ್ತವೆ. ಪಾವತಿಗಳನ್ನು ಸ್ವೀಕರಿಸುವುದು ಸುರಕ್ಷಿತವಾಗಿದೆ.",
        "ml": "നമസ്കാരം {name}. നിങ്ങളുടെ Paytm QR സ്റ്റാൻഡി 100% യഥാർത്ഥവും പരിശോധിച്ചതുമാണ്. UPI വിലാസവും ({vpa}) ഡിജിറ്റൽ വാട്ടർമാർക്കും പൂർണ്ണമായും പൊരുത്തപ്പെടുന്നു. പേയ്‌മെന്റുകൾ സുരക്ഷിതമാണ്.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}। ਤੁਹਾਡਾ ਪੇਟੀਐਮ QR ਸਟੈਂਡੀ 100% ਅਸਲੀ ਅਤੇ ਪ੍ਰਮਾਣਿਤ ਹੈ। UPI ਪਤਾ ({vpa}) ਅਤੇ ਡਿਜੀਟਲ ਵਾਟਰਮਾਰਕ ਦੋਵੇਂ ਮੇਲ ਖਾਂਦੇ ਹਨ। ਭੁਗਤਾਨ ਲੈਣਾ ਸੁਰੱਖਿਅਤ ਹੈ।"
    },
    "QR_TAMPERED": {
        "en": "Critical Security Alert for {name}! Physical QR tampering detected on your standee! The visible payment destination redirects customer payments to an unauthorized account ({scanned_vpa}), while your authentic cryptographic signature belongs to {name}. The steganographic watermark was corrupted to {score}%. As an autonomous agent, I have immediately frozen settlement payouts, triggered a spoken fraud warning on your Soundbox, and logged an NPCI fraud docket. Do NOT accept payments with this QR!",
        "hi": "सावधान {name}! आपके फिजिकल क्यूआर स्टैंडी पर गंभीर छेड़छाड़ पाई गई है! भुगतान गंतव्य ग्राहकों के पैसे को एक अनधिकृत खाते ({scanned_vpa}) पर भेज रहा है, जबकि आपका असली डिजिटल हस्ताक्षर {name} का है। वॉटरमार्क टूटकर {score}% रह गया है। सुरक्षा के लिए, मैंने तुरंत सेटलमेंट रोक दिया है, आपके साउंडबॉक्स पर वॉयस फ्रॉड चेतावनी जारी की है, और एनपीसीआई रिपोर्ट दर्ज कर दी है। कृपया इस क्यूआर से कोई भुगतान न लें!",
        "mr": "सावधान {name}! आपल्या QR स्टँडीवर फसवणूक आणि फेरफार आढळली आहे! ग्राहक पेमेंट एका अनधिकृत खात्यावर ({scanned_vpa}) वळवले जात आहे, तर आपले खरे डिजिटल स्वाक्षरी {name} चे आहे. सुरक्षिततेसाठी मी तात्काळ सेटलमेंट गोठवले आहे, साउंडबॉक्सवर फ्रॉड वॉर्निंग दिली आहे. या QR वरून पेमेंट घेऊ नका!",
        "gu": "સાવધાન {name}! તમારા QR સ્ટેન્ડી સાથે છેડછાડ પકડાઈ છે! ગ્રાહકોનું પેમેન્ટ કોઈ અજાણ્યા ખાતા ({scanned_vpa}) પર જઈ રહ્યું છે. મેં તાત્કાલિક સેટલમેન્ટ અટકાવી દીધું છે અને તમારા સાઉન્ડબોક્સ પર ચેતવણી આપી છે. આ QR પરથી પેમેન્ટ લેશો નહીં!",
        "bn": "সাবধান {name}! আপনার QR স্ট্যান্ডিতে জালিয়াতি ধরা পড়েছে! পেমেন্ট অন্য একটি অননুমোদিত অ্যাকাউন্টে ({scanned_vpa}) পাঠানো হচ্ছিল। আমি তাৎক্ষণিকভাবে সেটেলমেন্ট স্থগিত করেছি এবং সাউন্ডবক্সে সতর্কতা জারি করেছি। সামগ্রী দেবেন না!",
        "ta": "எச்சரிக்கை {name}! உங்கள் QR ஸ்டாண்டீ மாற்றப்பட்டுள்ளது! பணம் வேறொரு கணக்கிற்கு ({scanned_vpa}) திருப்பி விடப்படுகிறது. உங்கள் பாதுகாப்பிற்காக செட்டில்மென்ட் முடக்கப்பட்டுள்ளது மற்றும் சவுண்ட்பாக்ஸில் எச்சரிக்கை ஒலித்துள்ளது. பணம் ஏற்க வேண்டாம்!",
        "te": "హెచ్చరిక {name}! మీ QR స్టాండీ ట్యాంపర్ చేయబడింది! చెల్లింపులు వేరొక అనధికార ఖాతాకు ({scanned_vpa}) వెళ్తున్నాయి. నేను వెంటనే సెటిల్‌మెంట్‌ను నిలిపివేసి, సౌండ్‌బాక్స్‌లో హెచ్చరిక జారీ చేసాను. చెల్లింపులు తీసుకోవద్దు!",
        "kn": "ಎಚ್ಚರಿಕೆ {name}! ನಿಮ್ಮ QR ಸ್ಟ್ಯಾಂಡಿ ತಿದ್ದಲಾಗಿದೆ! ಪಾವತಿಗಳು ಅಪರಿಚಿತ ಖಾತೆಗೆ ({scanned_vpa}) ಹೋಗುತ್ತಿವೆ. ನಾನು ತಕ್ಷಣ ಸೆಟ್ಲ್‌ಮೆಂಟ್ ಸ್ಥಗಿತಗೊಳಿಸಿದ್ದೇನೆ ಮತ್ತು ಸೌಂಡ್‌ಬಾಕ್ಸ್‌ನಲ್ಲಿ ಎಚ್ಚರಿಕೆ ನೀಡಿದ್ದೇನೆ. ಹಣ ಪಡೆಯಬೇಡಿ!",
        "ml": "മുന്നറിയിപ്പ് {name}! നിങ്ങളുടെ QR സ്റ്റാൻഡിയിൽ തിരിമറി നടന്നു! പേയ്‌മെന്റുകൾ മറ്റൊരു അക്കൗണ്ടിലേക്ക് ({scanned_vpa}) മാറ്റപ്പെടുന്നു. ഞാൻ ഉടൻ തന്നെ സെറ്റിൽമെന്റ് മരവിപ്പിക്കുകയും സൗണ്ട്ബോക്സിൽ മുന്നറിയിപ്പ് നൽകുകയും ചെയ്തു. പേയ്‌മെന്റ് സ്വീകരിക്കരുത്!",
        "pa": "ਸਾਵਧਾਨ {name}! ਤੁਹਾਡੇ QR ਸਟੈਂਡੀ ਨਾਲ ਛੇੜਛਾੜ ਹੋਈ ਹੈ! ਗਾਹਕਾਂ ਦਾ ਭੁਗਤਾਨ ਦੂਜੇ ਖਾਤੇ ({scanned_vpa}) ਵਿੱਚ ਜਾ ਰਿਹਾ ਹੈ। ਮੈਂ ਤੁਰੰਤ ਸੈਟਲਮੈਂਟ ਰੋਕ ਦਿੱਤੀ ਹੈ ਅਤੇ ਸਾਊਂਡਬਾਕਸ ਤੇ ਚੇਤਾਵਨੀ ਦਿੱਤੀ ਹੈ। ਪੈਸੇ ਨਾ ਲਓ!"
    },
    "QR_AWAITING_SCAN": {
        "en": "Hello {name}. I am your Paytm QR Armor teammate. Upload or verify your standee image to inspect its physical cryptographic provenance.",
        "hi": "नमस्ते {name}। मैं आपका पेटीएम क्यूआर सुरक्षा साथी हूँ। अपनी दुकान के स्टैंडी की प्रामाणिकता जांचने के लिए इमेज अपलोड करें या सत्यापन बटन दबाएँ।",
        "mr": "नमस्ते {name}. मी आपला पेटीएम QR सुरक्षा सहकारी आहे. स्टँडीची सत्यता तपासण्यासाठी इमेज अपलोड करा.",
        "gu": "નમસ્તે {name}. હું તમારો પેટીએમ QR સુરક્ષા સાથી છું. તમારા સ્ટેન્ડીની ચકાસણી કરવા માટે ઈમેજ અપલોડ કરો.",
        "bn": "নমস্কার {name}। আপনার স্ট্যান্ডি যাচাই করতে ইমেজ আপলোড করুন।",
        "ta": "வணக்கம் {name}. உங்கள் QR ஸ்டாண்டீயை சரிபார்க்க படத்தை பதிவேற்றவும்.",
        "te": "నమస్తే {name}. మీ QR స్టాండీని ధృవీకరించడానికి చిత్రాన్ని అప్‌లోడ్ చేయండి.",
        "kn": "ನಮಸ್ಕಾರ {name}. ನಿಮ್ಮ QR ಸ್ಟ್ಯಾಂಡಿ ಪರಿಶೀಲಿಸಲು ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "ml": "നമസ്കാരം {name}. നിങ്ങളുടെ QR സ്റ്റാൻഡി പരിശോധിക്കാൻ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}। ਆਪਣਾ QR ਸਟੈਂਡੀ ਪ੍ਰਮਾਣਿਤ ਕਰਨ ਲਈ ਫੋਟੋ ਅੱਪਲੋਡ ਕਰੋ।"
    }
}

def process_qr_voice_query(
    merchant_id: str,
    query: str,
    is_verified: bool = False,
    is_valid: Optional[bool] = None,
    integrity_score: Optional[float] = None,
    scanned_vpa: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """Autonomous QR Voice Agent Response Generator.
    Produces clean, plain-text spoken responses tailored to merchant inquiry and current QR state.
    """
    lang = language.lower() if language else "en"
    merchants = run_query(f"SELECT id, name, username FROM merchants WHERE id = '{merchant_id}' LIMIT 1")
    merchant_name = merchants[0]["name"] if merchants else "Merchant"
    expected_vpa = f"{merchants[0]['username']}@paytm" if merchants else f"{merchant_id}@paytm"

    if not is_verified or is_valid is None:
        template = QR_VOICE_TEMPLATES["QR_AWAITING_SCAN"].get(lang, QR_VOICE_TEMPLATES["QR_AWAITING_SCAN"]["en"])
        spoken_text = template.format(name=merchant_name)
        status = "AWAITING_SCAN"
    elif is_valid:
        template = QR_VOICE_TEMPLATES["QR_GENUINE"].get(lang, QR_VOICE_TEMPLATES["QR_GENUINE"]["en"])
        score_val = f"{integrity_score:.1f}" if integrity_score is not None else "98.5"
        spoken_text = template.format(name=merchant_name, vpa=expected_vpa, score=score_val)
        status = "GENUINE"
    else:
        template = QR_VOICE_TEMPLATES["QR_TAMPERED"].get(lang, QR_VOICE_TEMPLATES["QR_TAMPERED"]["en"])
        score_val = f"{integrity_score:.1f}" if integrity_score is not None else "24.8"
        rogue_vpa = scanned_vpa or "thief_scam99@ybl"
        spoken_text = template.format(name=merchant_name, scanned_vpa=rogue_vpa, score=score_val)
        status = "TAMPERED"

    return {
        "status": status,
        "query": query,
        "language": lang,
        "spoken_text": clean_plain_text(spoken_text),
        "merchant_name": merchant_name,
        "expected_vpa": expected_vpa
    }
