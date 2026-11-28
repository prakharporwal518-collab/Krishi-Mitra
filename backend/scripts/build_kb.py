"""Builds backend/data/diseases.json from compact definitions.

Each language block is: [name, about(cause), symptoms[], product, dosage, timing, organic[], prevention[]]
Run:  python scripts/build_kb.py
"""
import json
import re
from pathlib import Path

SAFETY = {
    "en": ["Wear gloves, mask and full sleeves while spraying", "Spray in the morning or evening, not against the wind", "Keep away from children, animals and water sources", "Follow the waiting period before harvest written on the label"],
    "hi": ["छिड़काव करते समय दस्ताने, मास्क और पूरी बाँह के कपड़े पहनें", "सुबह या शाम को छिड़काव करें, हवा के विपरीत नहीं", "बच्चों, पशुओं और पानी के स्रोतों से दूर रखें", "लेबल पर लिखी कटाई से पहले की प्रतीक्षा अवधि का पालन करें"],
    "mr": ["फवारणी करताना हातमोजे, मास्क आणि पूर्ण बाह्यांचे कपडे घाला", "सकाळी किंवा संध्याकाळी फवारणी करा, वाऱ्याच्या विरुद्ध दिशेने नाही", "मुले, जनावरे आणि पाण्याच्या स्रोतांपासून दूर ठेवा", "लेबलवर दिलेला काढणीपूर्व प्रतीक्षा कालावधी पाळा"],
}
WARNING = {
    "en": "Do not overuse pesticides or mix two chemicals in one tank unless the label allows it. Overuse causes resistance, harms soil, bees and your health. Use only the recommended dose.",
    "hi": "कीटनाशक का ज़्यादा उपयोग न करें और लेबल की अनुमति के बिना दो रसायन एक टंकी में न मिलाएँ। ज़्यादा उपयोग से प्रतिरोध बढ़ता है, मिट्टी, मधुमक्खियों और आपके स्वास्थ्य को नुकसान होता है। केवल सुझाई गई मात्रा का उपयोग करें।",
    "mr": "कीटकनाशकांचा अतिवापर करू नका आणि लेबलवर परवानगी नसल्यास दोन रसायने एका टाकीत मिसळू नका. अतिवापरामुळे प्रतिकारशक्ती वाढते, माती, मधमाश्या आणि तुमच्या आरोग्याला हानी होते. फक्त शिफारस केलेले प्रमाण वापरा.",
}

D = []


def E(id, crop, kind, pathogen, tags, src, en, hi, mr, region=None):
    D.append(dict(id=id, crop=crop, kind=kind, pathogen=pathogen, symptom_tags=tags, source=src, region_tips=region or [], L=dict(en=en, hi=hi, mr=mr)))


def tip(states, seasons, en, hi, mr):
    return {"states": states, "seasons": seasons, "tip": {"en": en, "hi": hi, "mr": mr}}


ICAR = "ICAR / State Agricultural University guideline"

# ---------------- TOMATO ----------------
E("tomato_early_blight", "tomato", "fungal", "Alternaria solani",
  ["brown_spots", "concentric_rings", "yellowing", "lower_leaves_first", "fruit_rot"], "ICAR-IIHR Bengaluru / TNAU Agritech",
  ["Tomato Early Blight", "A fungal disease caused by Alternaria solani. It spreads in warm, humid weather and from infected plant debris in the soil.",
   ["Dark brown spots with rings (like a target) on older leaves", "Yellowing around spots; leaves dry and fall", "Dark sunken patches near the fruit stalk"],
   "Mancozeb 75% WP", "2.5 g per litre of water (about 500 g in 200 L per acre)", "Spray at first sign of spots; repeat every 10–15 days, max 3 sprays",
   ["Spray neem oil 5 ml/L with a few drops of soap", "Spray Trichoderma viride 5 g/L or Pseudomonas fluorescens 10 g/L"],
   ["Remove and burn infected lower leaves", "Crop rotation with non-solanaceous crops for 2–3 years", "Stake plants and mulch to stop soil splash", "Avoid overhead irrigation"]],
  ["टमाटर का अगेती झुलसा", "यह अल्टरनेरिया सोलानी फफूंद से होने वाला रोग है। गर्म और नम मौसम में तथा मिट्टी में पड़े संक्रमित पौधों के अवशेषों से फैलता है।",
   ["पुरानी पत्तियों पर गोल छल्लों वाले गहरे भूरे धब्बे", "धब्बों के चारों ओर पीलापन; पत्तियाँ सूखकर गिरती हैं", "फल के डंठल के पास गहरे धँसे धब्बे"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर पानी (लगभग 500 ग्राम 200 लीटर में प्रति एकड़)", "धब्बे दिखते ही छिड़काव करें; 10–15 दिन पर दोहराएँ, अधिकतम 3 छिड़काव",
   ["नीम तेल 5 मि.ली./लीटर कुछ बूँद साबुन के साथ छिड़कें", "ट्राइकोडर्मा विरिडी 5 ग्राम/लीटर या स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["संक्रमित निचली पत्तियाँ तोड़कर जला दें", "2–3 साल तक फसल चक्र अपनाएँ", "पौधों को सहारा दें और मल्चिंग करें", "ऊपर से सिंचाई न करें"]],
  ["टोमॅटोवरील लवकर करपा", "हा अल्टरनेरिया सोलानी बुरशीमुळे होणारा रोग आहे. उष्ण, दमट हवामानात आणि जमिनीतील रोगट अवशेषांमुळे पसरतो.",
   ["जुन्या पानांवर वर्तुळाकार कड्यांचे गडद तपकिरी ठिपके", "ठिपक्यांभोवती पिवळेपणा; पाने वाळून गळतात", "फळाच्या देठाजवळ गडद खोलगट डाग"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर पाणी (सुमारे 500 ग्रॅम 200 लिटरमध्ये प्रति एकर)", "ठिपके दिसताच फवारणी करा; 10–15 दिवसांनी पुन्हा, जास्तीत जास्त 3 फवारण्या",
   ["निंबोळी तेल 5 मि.ली./लिटर थोड्या साबणासह फवारा", "ट्रायकोडर्मा 5 ग्रॅम/लिटर किंवा स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["रोगट खालची पाने काढून जाळा", "2–3 वर्षे पीक फेरपालट करा", "झाडांना आधार द्या आणि आच्छादन करा", "तुषार सिंचन टाळा"]],
  [tip(["Maharashtra", "Karnataka", "Andhra Pradesh", "Telangana"], ["kharif"],
       "Kharif tomato in the Deccan faces high humidity in July–Sept: start preventive Mancozeb sprays 30 days after transplanting.",
       "दक्कन क्षेत्र में खरीफ टमाटर में जुलाई–सितंबर में नमी अधिक रहती है: रोपाई के 30 दिन बाद से बचाव हेतु मैंकोज़ेब छिड़काव शुरू करें।",
       "दख्खन भागात खरीप टोमॅटोमध्ये जुलै–सप्टेंबरमध्ये आर्द्रता जास्त असते: लागवडीनंतर 30 दिवसांनी प्रतिबंधात्मक मॅन्कोझेब फवारणी सुरू करा.")])

E("tomato_late_blight", "tomato", "fungal", "Phytophthora infestans",
  ["water_soaked", "brown_spots", "leaf_blight", "white_mold_underside", "fruit_rot", "wilting"], "ICAR-IIHR / ICAR-CPRI advisory",
  ["Tomato Late Blight", "A fast-spreading water-mould disease (Phytophthora infestans). Cool nights, fog and rain help it destroy a field in a few days.",
   ["Large water-soaked, greyish-brown patches on leaves", "White fungal growth under leaves in the morning", "Firm brown greasy patches on fruits"],
   "Metalaxyl 8% + Mancozeb 64% WP", "2.5 g per litre (500 g per acre in 200 L water)", "Spray immediately when seen; repeat after 7–10 days in cloudy/rainy weather",
   ["Remove and destroy infected plants immediately", "Spray Pseudomonas fluorescens 10 g/L as a preventive"],
   ["Use healthy seedlings and resistant varieties (e.g., Arka Rakshak)", "Wide spacing and good drainage", "Do not plant near potato fields", "Preventive Mancozeb 2.5 g/L before forecast of cold, wet weather"]],
  ["टमाटर का पछेती झुलसा", "यह तेज़ी से फैलने वाला रोग (फाइटोफ्थोरा इन्फेस्टान्स) है। ठंडी रातें, कोहरा और बारिश में कुछ ही दिनों में पूरा खेत नष्ट कर सकता है।",
   ["पत्तियों पर बड़े पानी जैसे भूरे-धूसर धब्बे", "सुबह पत्तियों के नीचे सफेद फफूंद", "फलों पर सख्त भूरे चिकने धब्बे"],
   "Metalaxyl 8% + Mancozeb 64% WP (मेटालैक्सिल + मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर (500 ग्राम प्रति एकड़ 200 लीटर पानी में)", "दिखते ही तुरंत छिड़काव; बादल/बारिश में 7–10 दिन बाद दोहराएँ",
   ["संक्रमित पौधे तुरंत उखाड़कर नष्ट करें", "बचाव हेतु स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["स्वस्थ पौध और प्रतिरोधी किस्में (जैसे अर्का रक्षक) लगाएँ", "उचित दूरी और अच्छी जल निकासी", "आलू के खेत के पास न लगाएँ", "ठंडे-गीले मौसम के पूर्वानुमान पर मैंकोज़ेब 2.5 ग्राम/लीटर का बचाव छिड़काव"]],
  ["टोमॅटोवरील उशिरा करपा", "हा झपाट्याने पसरणारा रोग (फायटोफ्थोरा इन्फेस्टन्स) आहे. थंड रात्री, धुके आणि पावसात काही दिवसांत संपूर्ण शेत नष्ट करू शकतो.",
   ["पानांवर मोठे पाणथळ करड्या-तपकिरी रंगाचे डाग", "सकाळी पानांच्या खाली पांढरी बुरशी", "फळांवर कडक तपकिरी तेलकट डाग"],
   "Metalaxyl 8% + Mancozeb 64% WP (मेटॅलॅक्सिल + मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर (200 लिटर पाण्यात 500 ग्रॅम प्रति एकर)", "दिसताच त्वरित फवारणी; ढगाळ/पावसाळी हवामानात 7–10 दिवसांनी पुन्हा",
   ["रोगट झाडे त्वरित उपटून नष्ट करा", "प्रतिबंधासाठी स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["निरोगी रोपे आणि प्रतिकारक जाती (उदा. अर्का रक्षक) लावा", "योग्य अंतर आणि चांगला निचरा", "बटाट्याच्या शेताजवळ लागवड टाळा", "थंड-ओल्या हवामानाच्या अंदाजावर मॅन्कोझेब 2.5 ग्रॅम/लिटर प्रतिबंधात्मक फवारणी"]],
  [tip(["Himachal Pradesh", "Uttarakhand", "Karnataka", "Tamil Nadu"], ["rabi", "kharif"],
       "Hill and cool regions: late blight risk is highest during foggy, cold spells. Follow the local KVK blight forecast.",
       "पहाड़ी और ठंडे क्षेत्रों में कोहरे और ठंड के समय पछेती झुलसा का खतरा सबसे अधिक होता है। स्थानीय केवीके का पूर्वानुमान देखें।",
       "डोंगराळ व थंड भागात धुके व थंडीच्या काळात उशिरा करप्याचा धोका सर्वाधिक असतो. स्थानिक केव्हीकेचा अंदाज पाहा.")])

E("tomato_leaf_curl", "tomato", "viral", "Tomato Yellow Leaf Curl Virus (spread by whitefly)",
  ["leaf_curl", "yellowing", "stunted", "small_leaves", "insects_underside"], "ICAR-IIHR / ICAR-IIVR Varanasi",
  ["Tomato Leaf Curl Virus", "A virus disease spread by tiny white flies (whitefly). There is no cure for infected plants; control the whitefly to protect the rest of the crop.",
   ["Leaves curl upward and become small and crinkled", "Yellow leaf edges, plants stay short (stunted)", "Very few flowers and fruits", "Tiny white insects fly up when the plant is shaken"],
   "Imidacloprid 17.8% SL (for whitefly)", "0.3 ml per litre (60 ml per acre in 200 L water)", "Spray when whiteflies are seen; repeat after 15 days if needed. Alternate with Thiamethoxam 25% WG 0.3 g/L",
   ["Install 10–12 yellow sticky traps per acre", "Spray neem oil (1500 ppm) 5 ml/L every 7–10 days", "Grow 2 rows of maize/sorghum as a border barrier"],
   ["Raise seedlings under 40-mesh insect net", "Uproot and bury infected plants early", "Use tolerant varieties (e.g., Arka Rakshak, Arka Samrat)", "Remove weeds that host whitefly"]],
  ["टमाटर पत्ती मोड़क विषाणु रोग", "यह सफेद मक्खी से फैलने वाला विषाणु रोग है। संक्रमित पौधे का कोई इलाज नहीं है; बाकी फसल बचाने के लिए सफेद मक्खी का नियंत्रण करें।",
   ["पत्तियाँ ऊपर की ओर मुड़कर छोटी और सिकुड़ी हो जाती हैं", "पत्तियों के किनारे पीले, पौधा बौना रह जाता है", "फूल और फल बहुत कम लगते हैं", "पौधा हिलाने पर छोटी सफेद मक्खियाँ उड़ती हैं"],
   "Imidacloprid 17.8% SL (इमिडाक्लोप्रिड - सफेद मक्खी हेतु)", "0.3 मि.ली. प्रति लीटर (60 मि.ली. प्रति एकड़ 200 लीटर पानी में)", "सफेद मक्खी दिखने पर छिड़काव; ज़रूरत हो तो 15 दिन बाद दोहराएँ। थायमेथोक्साम 25% WG 0.3 ग्राम/लीटर से बदल-बदल कर",
   ["प्रति एकड़ 10–12 पीले चिपचिपे ट्रैप लगाएँ", "नीम तेल (1500 ppm) 5 मि.ली./लीटर हर 7–10 दिन पर छिड़कें", "खेत के किनारे मक्का/ज्वार की 2 कतारें लगाएँ"],
   ["पौध को 40-मेश कीटरोधी जाली में तैयार करें", "संक्रमित पौधे जल्दी उखाड़कर मिट्टी में दबा दें", "सहनशील किस्में (अर्का रक्षक, अर्का सम्राट) लगाएँ", "सफेद मक्खी को आश्रय देने वाले खरपतवार हटाएँ"]],
  ["टोमॅटोवरील पर्णगुच्छ (लीफ कर्ल) विषाणू", "हा पांढऱ्या माशीमुळे पसरणारा विषाणूजन्य रोग आहे. रोगट झाडावर उपाय नाही; उरलेले पीक वाचवण्यासाठी पांढऱ्या माशीचे नियंत्रण करा.",
   ["पाने वरच्या बाजूला वळतात, लहान व सुरकुतलेली होतात", "पानांच्या कडा पिवळ्या, झाड खुजे राहते", "फुले व फळे फार कमी लागतात", "झाड हलवल्यास लहान पांढऱ्या माश्या उडतात"],
   "Imidacloprid 17.8% SL (इमिडाक्लोप्रिड - पांढऱ्या माशीसाठी)", "0.3 मि.ली. प्रति लिटर (200 लिटर पाण्यात 60 मि.ली. प्रति एकर)", "पांढरी माशी दिसताच फवारणी; गरज असल्यास 15 दिवसांनी पुन्हा. थायामेथोक्झाम 25% WG 0.3 ग्रॅम/लिटर आलटून पालटून",
   ["एकरी 10–12 पिवळे चिकट सापळे लावा", "निंबोळी तेल (1500 ppm) 5 मि.ली./लिटर दर 7–10 दिवसांनी फवारा", "शेताच्या कडेने मका/ज्वारीच्या 2 ओळी लावा"],
   ["रोपे 40-मेश कीटकरोधी जाळीत तयार करा", "रोगट झाडे लवकर उपटून गाडून टाका", "सहनशील जाती (अर्का रक्षक, अर्का सम्राट) लावा", "पांढऱ्या माशीला आश्रय देणारे तण काढा"]],
  [tip(["Karnataka", "Maharashtra", "Andhra Pradesh", "Telangana", "Tamil Nadu"], ["zaid", "rabi"],
       "Whitefly populations peak in dry, warm months (Feb–May). Net-house nurseries are strongly advised for summer tomato.",
       "सूखे-गर्म महीनों (फरवरी–मई) में सफेद मक्खी सबसे ज़्यादा होती है। गर्मी के टमाटर के लिए जाली-घर नर्सरी ज़रूर अपनाएँ।",
       "कोरड्या-उष्ण महिन्यांत (फेब्रुवारी–मे) पांढरी माशी सर्वाधिक असते. उन्हाळी टोमॅटोसाठी जाळीगृहात रोपवाटिका करा.")])

E("tomato_bacterial_spot", "tomato", "bacterial", "Xanthomonas spp.",
  ["black_spots", "water_soaked", "yellowing", "fruit_spots"], ICAR,
  ["Tomato Bacterial Spot", "A bacterial disease (Xanthomonas) spread through infected seed, rain splash and wet hands/tools.",
   ["Small dark, greasy spots on leaves with yellow halo", "Spots join and leaves look burnt", "Raised scabby spots on fruits"],
   "Copper Oxychloride 50% WP", "3 g per litre (600 g per acre in 200 L water)", "Spray at first symptoms; repeat every 10 days in rainy weather (max 3)",
   ["Seed treatment with Pseudomonas fluorescens 10 g/kg seed", "Spray Pseudomonas fluorescens 10 g/L"],
   ["Use certified disease-free seed", "Do not work in the field when plants are wet", "Remove infected plant debris after harvest", "Rotate with cereals"]],
  ["टमाटर का जीवाणु धब्बा रोग", "यह जीवाणु (ज़ैंथोमोनास) रोग संक्रमित बीज, बारिश की छींटों और गीले हाथों/औज़ारों से फैलता है।",
   ["पत्तियों पर पीले घेरे वाले छोटे काले चिकने धब्बे", "धब्बे मिलकर पत्तियाँ झुलसी दिखती हैं", "फलों पर उभरे खुरदरे धब्बे"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सीक्लोराइड)", "3 ग्राम प्रति लीटर (600 ग्राम प्रति एकड़ 200 लीटर पानी में)", "पहले लक्षण पर छिड़काव; बरसात में हर 10 दिन पर दोहराएँ (अधिकतम 3)",
   ["स्यूडोमोनास 10 ग्राम/किलो बीज से बीज उपचार", "स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["प्रमाणित रोगमुक्त बीज लें", "पौधे गीले हों तो खेत में काम न करें", "कटाई के बाद संक्रमित अवशेष हटाएँ", "अनाज फसलों के साथ फसल चक्र"]],
  ["टोमॅटोवरील जिवाणूजन्य ठिपके", "हा जिवाणूजन्य (झँथोमोनास) रोग रोगट बियाणे, पावसाचे शिंतोडे आणि ओल्या हात/अवजारांमुळे पसरतो.",
   ["पानांवर पिवळ्या कड्याचे लहान काळे तेलकट ठिपके", "ठिपके एकत्र येऊन पाने करपलेली दिसतात", "फळांवर उंचवटलेले खडबडीत डाग"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सिक्लोराईड)", "3 ग्रॅम प्रति लिटर (200 लिटर पाण्यात 600 ग्रॅम प्रति एकर)", "पहिली लक्षणे दिसताच फवारणी; पावसाळ्यात दर 10 दिवसांनी (जास्तीत जास्त 3)",
   ["स्युडोमोनास 10 ग्रॅम/किलो बियाण्यास बीजप्रक्रिया", "स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["प्रमाणित रोगमुक्त बियाणे वापरा", "झाडे ओली असताना शेतात काम करू नका", "काढणीनंतर रोगट अवशेष नष्ट करा", "तृणधान्यांसोबत फेरपालट"]])

E("tomato_leaf_mold", "tomato", "fungal", "Passalora fulva",
  ["yellow_spots", "olive_mold_underside", "yellowing"], ICAR,
  ["Tomato Leaf Mould", "A fungal disease that grows in very humid, closed conditions like polyhouses and dense planting.",
   ["Pale yellow patches on upper leaf surface", "Olive-green to brown velvety mould under the leaf", "Leaves wither and drop"],
   "Chlorothalonil 75% WP", "2 g per litre (400 g per acre)", "Spray at first symptoms, repeat after 10–12 days",
   ["Spray Trichoderma 5 g/L", "Improve air flow by pruning lower leaves"],
   ["Ventilate polyhouses, keep humidity below 85%", "Wider spacing", "Avoid wetting leaves while watering"]],
  ["टमाटर का पत्ती फफूंद रोग", "यह फफूंद रोग पॉलीहाउस और घनी बुवाई जैसी बहुत नम, बंद जगहों में बढ़ता है।",
   ["पत्ती की ऊपरी सतह पर हल्के पीले धब्बे", "पत्ती के नीचे जैतूनी-हरी से भूरी मखमली फफूंद", "पत्तियाँ मुरझाकर गिरती हैं"],
   "Chlorothalonil 75% WP (क्लोरोथालोनिल)", "2 ग्राम प्रति लीटर (400 ग्राम प्रति एकड़)", "पहले लक्षण पर छिड़काव, 10–12 दिन बाद दोहराएँ",
   ["ट्राइकोडर्मा 5 ग्राम/लीटर छिड़कें", "निचली पत्तियाँ छाँटकर हवा का संचार बढ़ाएँ"],
   ["पॉलीहाउस में हवा आने दें, नमी 85% से कम रखें", "अधिक दूरी पर बुवाई", "सिंचाई में पत्तियाँ गीली न करें"]],
  ["टोमॅटोवरील पानांवरील बुरशी", "हा बुरशीजन्य रोग पॉलीहाऊस व दाट लागवडीसारख्या अतिदमट, बंद जागी वाढतो.",
   ["पानाच्या वरच्या बाजूस फिकट पिवळे डाग", "पानाखाली ऑलिव्ह-हिरवी ते तपकिरी मखमली बुरशी", "पाने सुकून गळतात"],
   "Chlorothalonil 75% WP (क्लोरोथॅलोनिल)", "2 ग्रॅम प्रति लिटर (400 ग्रॅम प्रति एकर)", "पहिली लक्षणे दिसताच फवारणी, 10–12 दिवसांनी पुन्हा",
   ["ट्रायकोडर्मा 5 ग्रॅम/लिटर फवारा", "खालची पाने छाटून हवा खेळती ठेवा"],
   ["पॉलीहाऊसमध्ये वायुवीजन, आर्द्रता 85% पेक्षा कमी ठेवा", "जास्त अंतरावर लागवड", "पाणी देताना पाने ओली करू नका"]])

E("tomato_septoria_leaf_spot", "tomato", "fungal", "Septoria lycopersici",
  ["brown_spots", "small_spots_grey_center", "yellowing", "lower_leaves_first"], ICAR,
  ["Tomato Septoria Leaf Spot", "A fungal disease that spreads by rain splash from infected debris and weeds.",
   ["Many small round spots with grey centre and dark border", "Starts on lower leaves, moves upward", "Heavy leaf fall"],
   "Mancozeb 75% WP", "2.5 g per litre", "Spray at first spots; repeat every 10–14 days",
   ["Neem oil 5 ml/L", "Remove infected leaves regularly"],
   ["Crop rotation 2 years", "Mulch to prevent soil splash", "Remove solanaceous weeds"]],
  ["टमाटर का सेप्टोरिया पत्ती धब्बा", "यह फफूंद रोग संक्रमित अवशेषों और खरपतवारों से बारिश की छींटों द्वारा फैलता है।",
   ["धूसर बीच और गहरे किनारे वाले कई छोटे गोल धब्बे", "निचली पत्तियों से शुरू होकर ऊपर बढ़ता है", "पत्तियाँ बहुत झड़ती हैं"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर", "पहले धब्बे पर छिड़काव; हर 10–14 दिन पर दोहराएँ",
   ["नीम तेल 5 मि.ली./लीटर", "संक्रमित पत्तियाँ नियमित हटाएँ"],
   ["2 साल का फसल चक्र", "मिट्टी की छींटों से बचाने हेतु मल्चिंग", "बैंगन-कुल के खरपतवार हटाएँ"]],
  ["टोमॅटोवरील सेप्टोरिया पानठिपके", "हा बुरशीजन्य रोग रोगट अवशेष व तणांवरून पावसाच्या शिंतोड्यांनी पसरतो.",
   ["करडा मध्य व गडद कडा असलेले अनेक लहान गोल ठिपके", "खालच्या पानांपासून सुरू होऊन वर पसरतो", "पानांची मोठी गळ"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर", "पहिले ठिपके दिसताच फवारणी; दर 10–14 दिवसांनी पुन्हा",
   ["निंबोळी तेल 5 मि.ली./लिटर", "रोगट पाने नियमित काढा"],
   ["2 वर्षे फेरपालट", "आच्छादनाने मातीचे शिंतोडे थांबवा", "वांगी-कुळातील तण काढा"]])

E("tomato_spider_mites", "tomato", "pest", "Two-spotted spider mite (Tetranychus urticae)",
  ["yellow_spots", "webbing", "yellowing", "insects_underside", "leaf_bronzing"], "ICAR-NBAIR / TNAU Agritech",
  ["Tomato Spider Mites", "Tiny red/green mites suck sap from the underside of leaves. They multiply fast in hot, dry weather.",
   ["Fine yellow-white dots (stippling) on leaves", "Thin silky webbing under leaves", "Leaves turn bronze, dry and fall"],
   "Fenazaquin 10% EC (miticide)", "2 ml per litre (400 ml per acre)", "Spray under leaf surface when mites are seen; repeat after 10–15 days with a different miticide (e.g., Spiromesifen 22.9% SC 0.8 ml/L)",
   ["Spray strong water jet under leaves", "Neem oil 5 ml/L or wettable sulphur 80% WP 2 g/L"],
   ["Keep field weed-free", "Avoid water stress in hot weather", "Avoid excess synthetic pyrethroid sprays (they increase mites)"]],
  ["टमाटर में लाल मकड़ी (माइट)", "बहुत छोटी लाल/हरी मकड़ियाँ पत्तियों के नीचे से रस चूसती हैं। गर्म, सूखे मौसम में तेज़ी से बढ़ती हैं।",
   ["पत्तियों पर बारीक पीले-सफेद बिंदु", "पत्तियों के नीचे पतला रेशमी जाला", "पत्तियाँ कांसे जैसी होकर सूखकर गिरती हैं"],
   "Fenazaquin 10% EC (फेनाज़ाक्विन - माइटनाशक)", "2 मि.ली. प्रति लीटर (400 मि.ली. प्रति एकड़)", "माइट दिखने पर पत्ती के नीचे छिड़कें; 10–15 दिन बाद दूसरी दवा (स्पाइरोमेसिफेन 22.9% SC 0.8 मि.ली./लीटर) से दोहराएँ",
   ["पत्तियों के नीचे पानी की तेज़ धार मारें", "नीम तेल 5 मि.ली./लीटर या घुलनशील गंधक 80% WP 2 ग्राम/लीटर"],
   ["खेत खरपतवार मुक्त रखें", "गर्मी में पानी की कमी न होने दें", "सिंथेटिक पाइरेथ्रॉइड का अधिक छिड़काव न करें (माइट बढ़ते हैं)"]],
  ["टोमॅटोवरील कोळी (माइट)", "अतिशय लहान लाल/हिरवे कोळी पानांच्या खालून रस शोषतात. उष्ण, कोरड्या हवामानात झपाट्याने वाढतात.",
   ["पानांवर बारीक पिवळसर-पांढरे ठिपके", "पानांखाली पातळ रेशमी जाळे", "पाने कांस्य रंगाची होऊन वाळून गळतात"],
   "Fenazaquin 10% EC (फेनाझाक्विन - कोळीनाशक)", "2 मि.ली. प्रति लिटर (400 मि.ली. प्रति एकर)", "कोळी दिसताच पानांच्या खाली फवारा; 10–15 दिवसांनी दुसऱ्या औषधाने (स्पायरोमेसिफेन 22.9% SC 0.8 मि.ली./लिटर) पुन्हा",
   ["पानांखाली पाण्याचा जोरदार फवारा मारा", "निंबोळी तेल 5 मि.ली./लिटर किंवा पाण्यात मिसळणारे गंधक 80% WP 2 ग्रॅम/लिटर"],
   ["शेत तणमुक्त ठेवा", "उन्हाळ्यात पाण्याचा ताण पडू देऊ नका", "सिंथेटिक पायरेथ्रॉइडचा अतिवापर टाळा (कोळी वाढतात)"]])

E("tomato_target_spot", "tomato", "fungal", "Corynespora cassiicola",
  ["brown_spots", "concentric_rings", "fruit_spots"], ICAR,
  ["Tomato Target Spot", "A fungal disease favoured by warm, wet weather and dense canopy.",
   ["Brown spots with light centre and rings on leaves", "Spots on stems and sunken spots on fruit", "Leaves dry from bottom upward"],
   "Azoxystrobin 23% SC", "1 ml per litre (200 ml per acre)", "Spray at first symptoms; repeat after 15 days (max 2 sprays per season)",
   ["Trichoderma 5 g/L spray", "Prune lower leaves for air flow"],
   ["Avoid dense planting", "Remove crop debris", "Rotate crops"]],
  ["टमाटर का टारगेट स्पॉट", "यह फफूंद रोग गर्म, गीले मौसम और घनी फसल में बढ़ता है।",
   ["पत्तियों पर हल्के बीच और छल्लों वाले भूरे धब्बे", "तने पर धब्बे और फलों पर धँसे धब्बे", "पत्तियाँ नीचे से ऊपर की ओर सूखती हैं"],
   "Azoxystrobin 23% SC (एज़ोक्सीस्ट्रोबिन)", "1 मि.ली. प्रति लीटर (200 मि.ली. प्रति एकड़)", "पहले लक्षण पर छिड़काव; 15 दिन बाद दोहराएँ (प्रति मौसम अधिकतम 2)",
   ["ट्राइकोडर्मा 5 ग्राम/लीटर छिड़काव", "हवा हेतु निचली पत्तियाँ छाँटें"],
   ["घनी बुवाई न करें", "फसल अवशेष हटाएँ", "फसल चक्र अपनाएँ"]],
  ["टोमॅटोवरील टार्गेट स्पॉट", "हा बुरशीजन्य रोग उष्ण, ओल्या हवामानात व दाट पिकात वाढतो.",
   ["पानांवर फिकट मध्य व कड्यांचे तपकिरी ठिपके", "खोडावर डाग व फळांवर खोलगट डाग", "पाने खालून वर वाळतात"],
   "Azoxystrobin 23% SC (ॲझोक्सिस्ट्रोबिन)", "1 मि.ली. प्रति लिटर (200 मि.ली. प्रति एकर)", "पहिली लक्षणे दिसताच फवारणी; 15 दिवसांनी पुन्हा (हंगामात जास्तीत जास्त 2)",
   ["ट्रायकोडर्मा 5 ग्रॅम/लिटर फवारणी", "हवेसाठी खालची पाने छाटा"],
   ["दाट लागवड टाळा", "पीक अवशेष काढा", "फेरपालट करा"]])

E("tomato_mosaic_virus", "tomato", "viral", "Tomato mosaic virus (ToMV)",
  ["mosaic", "leaf_curl", "stunted", "small_leaves"], ICAR,
  ["Tomato Mosaic Virus", "A virus that spreads by touch – hands, tools, and tobacco users. It survives in seeds and plant debris. There is no chemical cure.",
   ["Light and dark green patchy (mosaic) pattern on leaves", "Leaves become narrow, fern-like and wrinkled", "Uneven ripening of fruits"],
   "No chemical cure – do NOT spray fungicides", "—", "Uproot infected plants immediately and bury/burn them",
   ["Dip hands/tools in skimmed milk or soap water before handling plants", "Spray 10% raw milk solution on young plants to reduce spread"],
   ["Use certified seed; treat seed with 10% trisodium phosphate", "Do not smoke/chew tobacco while working in field", "Disinfect tools", "Grow resistant hybrids"]],
  ["टमाटर मोज़ेक विषाणु", "यह विषाणु छूने से फैलता है – हाथ, औज़ार और तंबाकू उपयोगकर्ता। बीज और अवशेषों में जीवित रहता है। कोई रासायनिक इलाज नहीं।",
   ["पत्तियों पर हल्के और गहरे हरे चितकबरे धब्बे", "पत्तियाँ पतली, सिकुड़ी हुई हो जाती हैं", "फल असमान रूप से पकते हैं"],
   "कोई रासायनिक इलाज नहीं – फफूंदनाशक न छिड़कें", "—", "संक्रमित पौधे तुरंत उखाड़कर दबा/जला दें",
   ["पौधे छूने से पहले हाथ/औज़ार मलाई रहित दूध या साबुन पानी में डुबोएँ", "छोटे पौधों पर 10% कच्चे दूध का घोल छिड़कें"],
   ["प्रमाणित बीज लें; 10% ट्राइसोडियम फॉस्फेट से बीज उपचार", "खेत में तंबाकू/बीड़ी का सेवन न करें", "औज़ार कीटाणुरहित करें", "प्रतिरोधी संकर किस्में लगाएँ"]],
  ["टोमॅटो मोझॅक विषाणू", "हा विषाणू स्पर्शाने पसरतो – हात, अवजारे आणि तंबाखू सेवन करणारे. बियाणे व अवशेषांत टिकतो. रासायनिक उपाय नाही.",
   ["पानांवर फिकट व गडद हिरवे चट्टेपट्टे (मोझॅक)", "पाने अरुंद, सुरकुतलेली होतात", "फळे असमान पिकतात"],
   "रासायनिक उपाय नाही – बुरशीनाशक फवारू नका", "—", "रोगट झाडे त्वरित उपटून गाडा/जाळा",
   ["झाडांना हात लावण्यापूर्वी हात/अवजारे साय काढलेल्या दुधात किंवा साबण पाण्यात बुडवा", "लहान रोपांवर 10% कच्च्या दुधाचे द्रावण फवारा"],
   ["प्रमाणित बियाणे; 10% ट्रायसोडियम फॉस्फेटने बीजप्रक्रिया", "शेतात तंबाखू/विडी सेवन करू नका", "अवजारे निर्जंतुक करा", "प्रतिकारक संकरित जाती लावा"]])

# ---------------- POTATO ----------------
E("potato_early_blight", "potato", "fungal", "Alternaria solani",
  ["brown_spots", "concentric_rings", "yellowing", "lower_leaves_first"], "ICAR-CPRI Shimla",
  ["Potato Early Blight", "A fungal disease (Alternaria solani) that attacks older leaves, mostly when plants are stressed or under-fed.",
   ["Dark brown spots with target-like rings on older leaves", "Yellowing around spots", "Leaves dry early, reducing tuber size"],
   "Mancozeb 75% WP", "2.5 g per litre (500–600 g per acre)", "Spray at first spots; repeat every 10–12 days",
   ["Neem oil 5 ml/L", "Balanced manuring with FYM and potash"],
   ["Use healthy seed tubers", "Balanced NPK – avoid nitrogen shortage", "Destroy crop debris after harvest"]],
  ["आलू का अगेती झुलसा", "यह फफूंद (अल्टरनेरिया सोलानी) रोग पुरानी पत्तियों पर लगता है, ज़्यादातर जब पौधे कमज़ोर या पोषण की कमी में हों।",
   ["पुरानी पत्तियों पर छल्लों वाले गहरे भूरे धब्बे", "धब्बों के चारों ओर पीलापन", "पत्तियाँ जल्दी सूखती हैं, कंद छोटे रहते हैं"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर (500–600 ग्राम प्रति एकड़)", "पहले धब्बे पर छिड़काव; हर 10–12 दिन पर दोहराएँ",
   ["नीम तेल 5 मि.ली./लीटर", "गोबर की खाद और पोटाश के साथ संतुलित पोषण"],
   ["स्वस्थ बीज कंद लें", "संतुलित NPK – नाइट्रोजन की कमी न हो", "कटाई के बाद अवशेष नष्ट करें"]],
  ["बटाट्यावरील लवकर करपा", "हा बुरशीजन्य (अल्टरनेरिया सोलानी) रोग जुन्या पानांवर येतो, मुख्यतः झाडे कमकुवत किंवा अन्नद्रव्यांची कमतरता असताना.",
   ["जुन्या पानांवर कड्यांचे गडद तपकिरी ठिपके", "ठिपक्यांभोवती पिवळेपणा", "पाने लवकर वाळतात, कंद लहान राहतात"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर (500–600 ग्रॅम प्रति एकर)", "पहिले ठिपके दिसताच फवारणी; दर 10–12 दिवसांनी पुन्हा",
   ["निंबोळी तेल 5 मि.ली./लिटर", "शेणखत व पोटॅशसह संतुलित खत"],
   ["निरोगी बेणे वापरा", "संतुलित NPK – नत्राची कमतरता टाळा", "काढणीनंतर अवशेष नष्ट करा"]])

E("potato_late_blight", "potato", "fungal", "Phytophthora infestans",
  ["water_soaked", "brown_spots", "leaf_blight", "white_mold_underside", "wilting", "tuber_rot"], "ICAR-CPRI Shimla",
  ["Potato Late Blight", "The most destructive potato disease (Phytophthora infestans). Cold, foggy, humid weather (10–20 °C) can destroy the crop within a week.",
   ["Water-soaked dark patches starting at leaf tips and edges", "White cottony growth under leaves", "Whole plant collapses with a bad smell; tubers get reddish-brown rot"],
   "Cymoxanil 8% + Mancozeb 64% WP", "3 g per litre (600 g per acre in 200 L water)", "Spray as soon as disease appears; repeat after 7–10 days. Before disease, preventive Mancozeb 2.5 g/L when fog/rain is forecast",
   ["Remove and destroy infected plants", "Earthing-up to protect tubers", "Spray Pseudomonas fluorescens 10 g/L preventively"],
   ["Use certified seed tubers and resistant varieties (Kufri Jyoti, Kufri Girdhari)", "Avoid excess irrigation in foggy weather", "Cut and remove haulms 10 days before harvest", "Follow CPRI 'Indo-Blightcast' advisories"]],
  ["आलू का पछेती झुलसा", "आलू का सबसे विनाशकारी रोग (फाइटोफ्थोरा)। ठंडा, कोहरे वाला नम मौसम (10–20 °C) एक सप्ताह में फसल नष्ट कर सकता है।",
   ["पत्तियों के सिरों और किनारों से पानी जैसे गहरे धब्बे", "पत्तियों के नीचे सफेद रुई जैसी फफूंद", "पूरा पौधा बदबू के साथ गिर जाता है; कंदों में लाल-भूरी सड़न"],
   "Cymoxanil 8% + Mancozeb 64% WP (साइमोक्सानिल + मैंकोज़ेब)", "3 ग्राम प्रति लीटर (600 ग्राम प्रति एकड़ 200 लीटर पानी में)", "रोग दिखते ही छिड़काव; 7–10 दिन बाद दोहराएँ। रोग से पहले कोहरे/बारिश के पूर्वानुमान पर मैंकोज़ेब 2.5 ग्राम/लीटर",
   ["संक्रमित पौधे निकालकर नष्ट करें", "कंद बचाने हेतु मिट्टी चढ़ाएँ", "बचाव हेतु स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["प्रमाणित बीज कंद और प्रतिरोधी किस्में (कुफरी ज्योति, कुफरी गिरधारी)", "कोहरे में अधिक सिंचाई न करें", "खुदाई से 10 दिन पहले डंठल काटें", "सीपीआरआई 'इंडो-ब्लाइटकास्ट' सलाह मानें"]],
  ["बटाट्यावरील उशिरा करपा", "बटाट्याचा सर्वात विनाशकारी रोग (फायटोफ्थोरा). थंड, धुक्याचे दमट हवामान (10–20 °C) एका आठवड्यात पीक नष्ट करू शकते.",
   ["पानांच्या टोकांवर व कडांवर पाणथळ गडद डाग", "पानांखाली पांढरी कापसासारखी बुरशी", "संपूर्ण झाड दुर्गंधीसह कोसळते; कंदांना लालसर-तपकिरी कूज"],
   "Cymoxanil 8% + Mancozeb 64% WP (सायमोक्सानिल + मॅन्कोझेब)", "3 ग्रॅम प्रति लिटर (200 लिटर पाण्यात 600 ग्रॅम प्रति एकर)", "रोग दिसताच फवारणी; 7–10 दिवसांनी पुन्हा. रोगापूर्वी धुके/पावसाच्या अंदाजावर मॅन्कोझेब 2.5 ग्रॅम/लिटर",
   ["रोगट झाडे काढून नष्ट करा", "कंद वाचवण्यासाठी भर द्या", "प्रतिबंधासाठी स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["प्रमाणित बेणे व प्रतिकारक जाती (कुफरी ज्योती, कुफरी गिरधारी)", "धुक्यात जास्त पाणी देऊ नका", "काढणीपूर्वी 10 दिवस वेल कापा", "सीपीआरआय 'इंडो-ब्लाइटकास्ट' सल्ला पाळा"]],
  [tip(["Uttar Pradesh", "Punjab", "Bihar", "West Bengal", "Haryana"], ["rabi"],
       "Indo-Gangetic plains: late blight usually appears Dec–Jan during fog. Begin preventive sprays when 2–3 foggy days are forecast.",
       "गंगा के मैदानी क्षेत्र: पछेती झुलसा आमतौर पर दिसंबर–जनवरी में कोहरे के समय आता है। 2–3 दिन कोहरे के पूर्वानुमान पर बचाव छिड़काव शुरू करें।",
       "गंगेच्या मैदानी प्रदेशात उशिरा करपा सहसा डिसेंबर–जानेवारीत धुक्यात येतो. 2–3 दिवस धुक्याचा अंदाज असल्यास प्रतिबंधात्मक फवारणी सुरू करा.")])

# ---------------- RICE ----------------
E("rice_blast", "rice", "fungal", "Magnaporthe oryzae",
  ["eye_shaped_spots", "brown_spots", "neck_rot", "leaf_blight"], "ICAR-NRRI Cuttack / ICAR-IIRR Hyderabad",
  ["Rice Blast", "A serious fungal disease (Magnaporthe oryzae). High nitrogen, cloudy weather, dew and cool nights favour it.",
   ["Eye/spindle-shaped spots with grey centre and brown border on leaves", "Neck of the panicle turns black and breaks (neck blast)", "Empty, chaffy grains"],
   "Tricyclazole 75% WP", "0.6 g per litre (120 g per acre in 200 L water)", "Spray at first leaf spots and again at 50% panicle emergence",
   ["Seed treatment with Pseudomonas fluorescens 10 g/kg", "Spray Pseudomonas fluorescens 10 g/L at tillering"],
   ["Grow resistant varieties (e.g., Pusa Basmati 1609, Improved Samba Mahsuri)", "Split nitrogen doses; avoid excess urea", "Remove grassy weeds on bunds", "Seed treatment with Carbendazim 2 g/kg"]],
  ["धान का झोंका (ब्लास्ट) रोग", "यह गंभीर फफूंद रोग है। अधिक नाइट्रोजन, बादल, ओस और ठंडी रातें इसे बढ़ाती हैं।",
   ["पत्तियों पर धूसर बीच और भूरे किनारे वाले आँख/नाव जैसे धब्बे", "बाली की गर्दन काली होकर टूट जाती है (गर्दन झोंका)", "दाने खाली, भूसे जैसे"],
   "Tricyclazole 75% WP (ट्राइसाइक्लाज़ोल)", "0.6 ग्राम प्रति लीटर (120 ग्राम प्रति एकड़ 200 लीटर पानी में)", "पत्तियों पर पहले धब्बे पर और 50% बाली निकलने पर दोबारा छिड़काव",
   ["स्यूडोमोनास 10 ग्राम/किलो से बीज उपचार", "कल्ले निकलते समय स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["प्रतिरोधी किस्में (पूसा बासमती 1609, उन्नत सांबा मसूरी) लगाएँ", "नाइट्रोजन किस्तों में दें; ज़्यादा यूरिया नहीं", "मेड़ों से घास वाले खरपतवार हटाएँ", "कार्बेन्डाज़िम 2 ग्राम/किलो से बीज उपचार"]],
  ["भातावरील करपा (ब्लास्ट)", "हा गंभीर बुरशीजन्य रोग आहे. जास्त नत्र, ढगाळ हवामान, दव आणि थंड रात्री याला अनुकूल.",
   ["पानांवर करडा मध्य व तपकिरी कडा असलेले डोळ्याच्या आकाराचे ठिपके", "लोंबीची मान काळी पडून मोडते (मान करपा)", "दाणे पोचट"],
   "Tricyclazole 75% WP (ट्रायसायक्लाझोल)", "0.6 ग्रॅम प्रति लिटर (200 लिटर पाण्यात 120 ग्रॅम प्रति एकर)", "पानांवर पहिले ठिपके दिसताच आणि 50% लोंबी बाहेर पडताना पुन्हा फवारणी",
   ["स्युडोमोनास 10 ग्रॅम/किलो बीजप्रक्रिया", "फुटवे येताना स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["प्रतिकारक जाती (पुसा बासमती 1609, सुधारित सांबा मसुरी) लावा", "नत्र हप्त्यांत द्या; जास्त युरिया टाळा", "बांधावरील गवतवर्गीय तण काढा", "कार्बेन्डाझिम 2 ग्रॅम/किलो बीजप्रक्रिया"]],
  [tip(["Odisha", "West Bengal", "Chhattisgarh", "Andhra Pradesh", "Tamil Nadu", "Karnataka"], ["kharif"],
       "Kharif paddy: blast risk rises in Aug–Sept with cloudy days and night temperature 20–24 °C. Scout fields weekly.",
       "खरीफ धान: अगस्त–सितंबर में बादल और रात का तापमान 20–24 °C होने पर झोंका का खतरा बढ़ता है। हर सप्ताह खेत देखें।",
       "खरीप भात: ऑगस्ट–सप्टेंबरमध्ये ढगाळ दिवस व रात्रीचे तापमान 20–24 °C असताना करप्याचा धोका वाढतो. दर आठवड्याला शेत पाहा."),
   tip(["Maharashtra"], ["kharif"],
       "Konkan and Vidarbha paddy: avoid excess nitrogen in heavy-rain areas; apply urea in 3 splits.",
       "कोंकण और विदर्भ धान: भारी बारिश वाले क्षेत्रों में अधिक नाइट्रोजन न दें; यूरिया 3 किस्तों में दें।",
       "कोकण व विदर्भ भात: जास्त पावसाच्या भागात जास्त नत्र टाळा; युरिया 3 हप्त्यांत द्या.")])

E("rice_brown_spot", "rice", "fungal", "Bipolaris oryzae",
  ["brown_spots", "small_spots_grey_center", "yellowing", "grain_discolor"], "ICAR-NRRI Cuttack",
  ["Rice Brown Spot", "A fungal disease (Bipolaris oryzae) common in poor, nutrient-deficient soils and drought-stressed fields.",
   ["Oval brown spots (sesame-seed like) with grey centre on leaves", "Spots on grains – discoloured grains", "Seedlings may dry in nursery"],
   "Mancozeb 75% WP", "2.5 g per litre (500 g per acre)", "Spray at first symptoms and at booting stage; or Propiconazole 25% EC 1 ml/L",
   ["Seed treatment with Trichoderma 4 g/kg or hot water (52 °C for 10 min)", "Apply well-decomposed FYM"],
   ["Correct potash and silicon deficiency", "Use healthy, treated seed", "Avoid water stress"]],
  ["धान का भूरा धब्बा रोग", "यह फफूंद रोग गरीब, पोषक तत्वों की कमी वाली मिट्टी और सूखे से प्रभावित खेतों में आम है।",
   ["पत्तियों पर तिल जैसे अंडाकार भूरे धब्बे, बीच में धूसर", "दानों पर धब्बे – बदरंग दाने", "नर्सरी में पौध सूख सकती है"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर (500 ग्राम प्रति एकड़)", "पहले लक्षण पर और गभोट अवस्था पर छिड़काव; या प्रोपिकोनाज़ोल 25% EC 1 मि.ली./लीटर",
   ["ट्राइकोडर्मा 4 ग्राम/किलो या गर्म पानी (52 °C, 10 मिनट) से बीज उपचार", "अच्छी सड़ी गोबर खाद डालें"],
   ["पोटाश और सिलिकॉन की कमी दूर करें", "स्वस्थ, उपचारित बीज लें", "पानी की कमी न होने दें"]],
  ["भातावरील तपकिरी ठिपके", "हा बुरशीजन्य रोग गरीब, अन्नद्रव्यांची कमतरता असलेल्या जमिनीत व पाण्याचा ताण असलेल्या शेतात सामान्य आहे.",
   ["पानांवर तिळासारखे अंडाकृती तपकिरी ठिपके, मध्य करडा", "दाण्यांवर डाग – रंगहीन दाणे", "रोपवाटिकेत रोपे वाळू शकतात"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर (500 ग्रॅम प्रति एकर)", "पहिली लक्षणे व पोटरी अवस्थेत फवारणी; किंवा प्रोपिकोनाझोल 25% EC 1 मि.ली./लिटर",
   ["ट्रायकोडर्मा 4 ग्रॅम/किलो किंवा गरम पाणी (52 °C, 10 मिनिटे) बीजप्रक्रिया", "चांगले कुजलेले शेणखत द्या"],
   ["पोटॅश व सिलिकॉनची कमतरता दूर करा", "निरोगी, प्रक्रिया केलेले बियाणे वापरा", "पाण्याचा ताण टाळा"]])

E("rice_bacterial_leaf_blight", "rice", "bacterial", "Xanthomonas oryzae pv. oryzae",
  ["yellowing", "leaf_blight", "wavy_margin_lesions", "wilting"], "ICAR-IIRR Hyderabad",
  ["Rice Bacterial Leaf Blight", "A bacterial disease spread by irrigation water, rain and wind, especially after storms and with heavy nitrogen.",
   ["Yellow-to-white stripes starting from leaf tip with wavy edges", "Leaves dry and turn straw coloured", "Young plants wilt (kresek)"],
   "Copper Hydroxide 77% WP", "2 g per litre (400 g per acre)", "Spray at first symptoms; repeat after 12–15 days. Drain the field for 2–3 days",
   ["Spray fresh cow-dung extract 20% (20 kg in 100 L, filtered)", "Pseudomonas fluorescens 10 g/L"],
   ["Grow resistant varieties (Improved Samba Mahsuri, Pusa Basmati 1718)", "Avoid excess nitrogen; apply potash", "Do not let water flow from infected to healthy fields", "Remove weed hosts and stubble"]],
  ["धान का जीवाणु पत्ती झुलसा", "यह जीवाणु रोग सिंचाई के पानी, बारिश और हवा से फैलता है, खासकर तूफान के बाद और अधिक नाइट्रोजन पर।",
   ["पत्ती के सिरे से शुरू लहरदार किनारे वाली पीली-सफेद धारियाँ", "पत्तियाँ सूखकर भूसे के रंग की", "छोटे पौधे मुरझा जाते हैं (क्रेसेक)"],
   "Copper Hydroxide 77% WP (कॉपर हाइड्रॉक्साइड)", "2 ग्राम प्रति लीटर (400 ग्राम प्रति एकड़)", "पहले लक्षण पर छिड़काव; 12–15 दिन बाद दोहराएँ। खेत का पानी 2–3 दिन निकाल दें",
   ["20% ताज़े गोबर का छना हुआ घोल (20 किलो 100 लीटर में) छिड़कें", "स्यूडोमोनास 10 ग्राम/लीटर"],
   ["प्रतिरोधी किस्में (उन्नत सांबा मसूरी, पूसा बासमती 1718)", "अधिक नाइट्रोजन न दें; पोटाश डालें", "संक्रमित खेत का पानी स्वस्थ खेत में न जाने दें", "खरपतवार और ठूँठ हटाएँ"]],
  ["भातावरील जिवाणूजन्य करपा", "हा जिवाणूजन्य रोग सिंचनाचे पाणी, पाऊस आणि वाऱ्याने पसरतो, विशेषतः वादळानंतर व जास्त नत्रावर.",
   ["पानाच्या टोकापासून सुरू होणारे लहरी कडांचे पिवळे-पांढरे पट्टे", "पाने वाळून गवताच्या रंगाची होतात", "लहान रोपे मलूल होतात (क्रेसेक)"],
   "Copper Hydroxide 77% WP (कॉपर हायड्रॉक्साईड)", "2 ग्रॅम प्रति लिटर (400 ग्रॅम प्रति एकर)", "पहिली लक्षणे दिसताच फवारणी; 12–15 दिवसांनी पुन्हा. शेतातील पाणी 2–3 दिवस काढून टाका",
   ["20% ताज्या शेणाचा गाळलेला अर्क (20 किलो 100 लिटरमध्ये) फवारा", "स्युडोमोनास 10 ग्रॅम/लिटर"],
   ["प्रतिकारक जाती (सुधारित सांबा मसुरी, पुसा बासमती 1718)", "जास्त नत्र टाळा; पोटॅश द्या", "रोगट शेताचे पाणी निरोगी शेतात जाऊ देऊ नका", "तण व धसकटे काढा"]])

# ---------------- WHEAT ----------------
E("wheat_rust", "wheat", "fungal", "Puccinia striiformis / P. triticina",
  ["rust_pustules", "yellow_stripes", "yellowing"], "ICAR-IIWBR Karnal",
  ["Wheat Rust (Yellow / Brown)", "Fungal rust diseases spread by wind-blown spores. Yellow rust likes cool, humid weather (10–15 °C) in North India; brown rust appears in warmer weather.",
   ["Yellow powdery stripes on leaves (yellow rust)", "Orange-brown round pustules scattered on leaves (brown rust)", "Powder sticks to fingers when leaf is rubbed"],
   "Propiconazole 25% EC", "1 ml per litre (200 ml per acre in 200 L water)", "Spray as soon as first rust is seen; repeat after 15–20 days if needed. Alternative: Tebuconazole 25.9% EC 1 ml/L",
   ["Remove volunteer wheat plants and grass hosts", "Avoid late sowing"],
   ["Grow resistant varieties (HD 3226, DBW 187, PBW 826)", "Do not grow old susceptible varieties like PBW 343", "Timely sowing (Nov 1–25)", "Balanced nitrogen"]],
  ["गेहूँ का रतुआ (पीला / भूरा)", "हवा से उड़ने वाले बीजाणुओं से फैलने वाले फफूंद रोग। पीला रतुआ उत्तर भारत में ठंडे, नम मौसम (10–15 °C) में; भूरा रतुआ गर्म मौसम में आता है।",
   ["पत्तियों पर पीले पाउडर जैसी धारियाँ (पीला रतुआ)", "पत्तियों पर बिखरे नारंगी-भूरे गोल फफोले (भूरा रतुआ)", "पत्ती रगड़ने पर पाउडर उँगलियों पर लगता है"],
   "Propiconazole 25% EC (प्रोपिकोनाज़ोल)", "1 मि.ली. प्रति लीटर (200 मि.ली. प्रति एकड़ 200 लीटर पानी में)", "पहला रतुआ दिखते ही छिड़काव; ज़रूरत हो तो 15–20 दिन बाद दोहराएँ। विकल्प: टेबुकोनाज़ोल 25.9% EC 1 मि.ली./लीटर",
   ["अपने-आप उगे गेहूँ के पौधे और घास हटाएँ", "देर से बुवाई न करें"],
   ["प्रतिरोधी किस्में (HD 3226, DBW 187, PBW 826) लगाएँ", "पुरानी संवेदनशील किस्में जैसे PBW 343 न लगाएँ", "समय पर बुवाई (1–25 नवंबर)", "संतुलित नाइट्रोजन"]],
  ["गव्हावरील तांबेरा (पिवळा / तपकिरी)", "वाऱ्याने उडणाऱ्या बीजाणूंमुळे पसरणारे बुरशीजन्य रोग. पिवळा तांबेरा उत्तर भारतात थंड, दमट हवामानात (10–15 °C); तपकिरी तांबेरा उष्ण हवामानात येतो.",
   ["पानांवर पिवळ्या भुकटीसारखे पट्टे (पिवळा तांबेरा)", "पानांवर विखुरलेले नारिंगी-तपकिरी गोल फोड (तपकिरी तांबेरा)", "पान चोळल्यास भुकटी बोटांना लागते"],
   "Propiconazole 25% EC (प्रोपिकोनाझोल)", "1 मि.ली. प्रति लिटर (200 लिटर पाण्यात 200 मि.ली. प्रति एकर)", "पहिला तांबेरा दिसताच फवारणी; गरज असल्यास 15–20 दिवसांनी पुन्हा. पर्याय: टेब्युकोनाझोल 25.9% EC 1 मि.ली./लिटर",
   ["आपोआप उगवलेली गव्हाची रोपे व गवत काढा", "उशिरा पेरणी टाळा"],
   ["प्रतिकारक जाती (HD 3226, DBW 187, PBW 826) लावा", "PBW 343 सारख्या जुन्या संवेदनशील जाती टाळा", "वेळेवर पेरणी (1–25 नोव्हेंबर)", "संतुलित नत्र"]],
  [tip(["Punjab", "Haryana", "Himachal Pradesh", "Uttarakhand", "Jammu and Kashmir"], ["rabi"],
       "North-western plains & foothills: yellow rust appears Jan–Feb. Check fields near tree lines and foothills first.",
       "उत्तर-पश्चिमी मैदान और तराई: पीला रतुआ जनवरी–फरवरी में आता है। पेड़ों की कतारों और तराई के पास के खेत पहले जाँचें।",
       "उत्तर-पश्चिम मैदाने व पायथ्याचा भाग: पिवळा तांबेरा जानेवारी–फेब्रुवारीत येतो. झाडांच्या रांगा व पायथ्याजवळील शेते आधी तपासा."),
   tip(["Madhya Pradesh", "Maharashtra", "Karnataka", "Gujarat"], ["rabi"],
       "Central & peninsular zone: brown and black rust are more common. Grow zone-recommended varieties like HI 1634 / MACS 6478.",
       "मध्य और प्रायद्वीपीय क्षेत्र: भूरा और काला रतुआ अधिक होता है। क्षेत्र हेतु अनुशंसित किस्में जैसे HI 1634 / MACS 6478 लगाएँ।",
       "मध्य व द्वीपकल्पीय विभाग: तपकिरी व काळा तांबेरा जास्त आढळतो. विभागासाठी शिफारस केलेल्या जाती जसे HI 1634 / MACS 6478 लावा.")])

E("wheat_powdery_mildew", "wheat", "fungal", "Blumeria graminis f. sp. tritici",
  ["white_powder", "yellowing"], "ICAR-IIWBR Karnal",
  ["Wheat Powdery Mildew", "A fungal disease favoured by cool, cloudy, humid weather and dense crop with high nitrogen.",
   ["White to grey powdery patches on leaves and stems", "Leaves turn yellow and dry", "Small black dots inside old patches"],
   "Propiconazole 25% EC", "1 ml per litre (200 ml per acre)", "Spray when first patches appear; repeat after 15 days if needed",
   ["Wettable sulphur 80% WP 2 g/L", "Avoid excess nitrogen"],
   ["Resistant varieties", "Proper spacing and timely sowing", "Balanced fertiliser"]],
  ["गेहूँ का चूर्णिल आसिता", "यह फफूंद रोग ठंडे, बादल वाले नम मौसम और अधिक नाइट्रोजन वाली घनी फसल में बढ़ता है।",
   ["पत्तियों और तनों पर सफेद-धूसर पाउडर जैसे धब्बे", "पत्तियाँ पीली होकर सूखती हैं", "पुराने धब्बों में छोटे काले बिंदु"],
   "Propiconazole 25% EC (प्रोपिकोनाज़ोल)", "1 मि.ली. प्रति लीटर (200 मि.ली. प्रति एकड़)", "पहले धब्बे दिखने पर छिड़काव; ज़रूरत हो तो 15 दिन बाद दोहराएँ",
   ["घुलनशील गंधक 80% WP 2 ग्राम/लीटर", "अधिक नाइट्रोजन न दें"],
   ["प्रतिरोधी किस्में", "उचित दूरी और समय पर बुवाई", "संतुलित खाद"]],
  ["गव्हावरील भुरी", "हा बुरशीजन्य रोग थंड, ढगाळ, दमट हवामानात व जास्त नत्र असलेल्या दाट पिकात वाढतो.",
   ["पाने व खोडावर पांढरे-करडे भुकटीसारखे चट्टे", "पाने पिवळी पडून वाळतात", "जुन्या चट्ट्यांत लहान काळे ठिपके"],
   "Propiconazole 25% EC (प्रोपिकोनाझोल)", "1 मि.ली. प्रति लिटर (200 मि.ली. प्रति एकर)", "पहिले चट्टे दिसताच फवारणी; गरज असल्यास 15 दिवसांनी पुन्हा",
   ["पाण्यात मिसळणारे गंधक 80% WP 2 ग्रॅम/लिटर", "जास्त नत्र टाळा"],
   ["प्रतिकारक जाती", "योग्य अंतर व वेळेवर पेरणी", "संतुलित खत"]])

# ---------------- COTTON ----------------
E("cotton_leaf_curl", "cotton", "viral", "Cotton leaf curl virus (spread by whitefly)",
  ["leaf_curl", "vein_thickening", "leaf_enations", "stunted", "insects_underside"], "ICAR-CICR Nagpur",
  ["Cotton Leaf Curl Virus", "A virus disease spread by whitefly, very serious in North India (Punjab, Haryana, Rajasthan). Infected plants cannot be cured.",
   ["Upward or downward curling of leaves", "Thickened dark green veins; small leaf-like growths (enations) under leaves", "Stunted plants with few bolls"],
   "Diafenthiuron 50% WP (for whitefly)", "1.2 g per litre (240 g per acre)", "Spray when whitefly crosses 6–8 adults per leaf; alternate with Pyriproxyfen 10% EC 1 ml/L or Flonicamid 50% WG 0.3 g/L",
   ["Yellow sticky traps 10–15 per acre", "Neem oil (1500 ppm) 5 ml/L", "Uproot infected plants early in season"],
   ["Grow tolerant Bt hybrids recommended for your zone", "Timely sowing (April–mid May in North India)", "Remove weed hosts (Kanghi buti, Bhindi near field)", "Avoid early use of synthetic pyrethroids"]],
  ["कपास का पत्ती मरोड़ विषाणु", "सफेद मक्खी से फैलने वाला विषाणु रोग, उत्तर भारत (पंजाब, हरियाणा, राजस्थान) में बहुत गंभीर। संक्रमित पौधे ठीक नहीं होते।",
   ["पत्तियाँ ऊपर या नीचे की ओर मुड़ती हैं", "मोटी गहरी हरी नसें; पत्तियों के नीचे छोटी पत्ती जैसी वृद्धि", "बौने पौधे, कम टिंडे"],
   "Diafenthiuron 50% WP (डायफेंथियूरॉन - सफेद मक्खी हेतु)", "1.2 ग्राम प्रति लीटर (240 ग्राम प्रति एकड़)", "सफेद मक्खी 6–8 प्रति पत्ती से अधिक होने पर छिड़काव; पाइरीप्रॉक्सीफेन 10% EC 1 मि.ली./लीटर या फ्लोनिकामिड 50% WG 0.3 ग्राम/लीटर से बदलें",
   ["प्रति एकड़ 10–15 पीले चिपचिपे ट्रैप", "नीम तेल (1500 ppm) 5 मि.ली./लीटर", "मौसम की शुरुआत में संक्रमित पौधे उखाड़ें"],
   ["अपने क्षेत्र हेतु अनुशंसित सहनशील बीटी संकर लगाएँ", "समय पर बुवाई (उत्तर भारत में अप्रैल–मध्य मई)", "खरपतवार (कंघी बूटी, खेत के पास भिंडी) हटाएँ", "शुरुआत में सिंथेटिक पाइरेथ्रॉइड न डालें"]],
  ["कापसावरील पर्णगुच्छ विषाणू", "पांढऱ्या माशीमुळे पसरणारा विषाणूजन्य रोग, उत्तर भारतात (पंजाब, हरियाणा, राजस्थान) अतिशय गंभीर. रोगट झाडे बरी होत नाहीत.",
   ["पाने वर किंवा खाली वळतात", "जाड गडद हिरव्या शिरा; पानांखाली लहान पानासारखी वाढ", "खुजी झाडे, कमी बोंडे"],
   "Diafenthiuron 50% WP (डायफेंथ्युरॉन - पांढऱ्या माशीसाठी)", "1.2 ग्रॅम प्रति लिटर (240 ग्रॅम प्रति एकर)", "पांढरी माशी प्रति पान 6–8 पेक्षा जास्त झाल्यास फवारणी; पायरीप्रॉक्सीफेन 10% EC 1 मि.ली./लिटर किंवा फ्लोनिकॅमिड 50% WG 0.3 ग्रॅम/लिटरने आलटून पालटून",
   ["एकरी 10–15 पिवळे चिकट सापळे", "निंबोळी तेल (1500 ppm) 5 मि.ली./लिटर", "हंगामाच्या सुरुवातीला रोगट झाडे उपटा"],
   ["आपल्या विभागासाठी शिफारस केलेले सहनशील बीटी संकरित वाण लावा", "वेळेवर पेरणी", "तण (कंघी, शेताजवळील भेंडी) काढा", "सुरुवातीला सिंथेटिक पायरेथ्रॉइड टाळा"]],
  [tip(["Punjab", "Haryana", "Rajasthan"], ["kharif"],
       "North cotton zone: CLCuD is the main threat. Complete sowing by mid-May and monitor whitefly twice a week from June.",
       "उत्तरी कपास क्षेत्र: पत्ती मरोड़ मुख्य खतरा है। मध्य मई तक बुवाई पूरी करें और जून से सप्ताह में दो बार सफेद मक्खी की निगरानी करें।",
       "उत्तर कापूस विभाग: पर्णगुच्छ हा मुख्य धोका आहे. मे मध्यापर्यंत पेरणी पूर्ण करा व जूनपासून आठवड्यातून दोनदा पांढऱ्या माशीची पाहणी करा."),
   tip(["Maharashtra", "Telangana", "Gujarat", "Madhya Pradesh"], ["kharif"],
       "Central zone: leaf curl is less common, but watch for pink bollworm – use pheromone traps 5 per acre.",
       "मध्य क्षेत्र: पत्ती मरोड़ कम है, पर गुलाबी सुंडी पर नज़र रखें – प्रति एकड़ 5 फेरोमोन ट्रैप लगाएँ।",
       "मध्य विभाग: पर्णगुच्छ कमी आढळतो, पण गुलाबी बोंडअळीवर लक्ष ठेवा – एकरी 5 कामगंध सापळे लावा.")])

E("cotton_bacterial_blight", "cotton", "bacterial", "Xanthomonas citri pv. malvacearum",
  ["water_soaked", "angular_spots", "black_spots", "vein_blackening"], "ICAR-CICR Nagpur",
  ["Cotton Bacterial Blight (Angular Leaf Spot)", "A bacterial disease spread through seed and rain splash in warm, humid weather.",
   ["Angular water-soaked spots between veins that turn brown-black", "Blackening along veins", "Black lesions on stems and bolls; bolls rot"],
   "Copper Oxychloride 50% WP", "2.5 g per litre (500 g per acre)", "Spray at first symptoms; repeat after 15 days",
   ["Seed treatment with Pseudomonas fluorescens 10 g/kg", "Remove infected leaves"],
   ["Use delinted, treated seed", "Remove and destroy crop residue", "Avoid excess nitrogen and waterlogging"]],
  ["कपास का जीवाणु झुलसा (कोणीय पत्ती धब्बा)", "यह जीवाणु रोग बीज और बारिश की छींटों से गर्म, नम मौसम में फैलता है।",
   ["नसों के बीच कोणीय पानी जैसे धब्बे जो भूरे-काले होते हैं", "नसों के साथ कालापन", "तनों और टिंडों पर काले धब्बे; टिंडे सड़ते हैं"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सीक्लोराइड)", "2.5 ग्राम प्रति लीटर (500 ग्राम प्रति एकड़)", "पहले लक्षण पर छिड़काव; 15 दिन बाद दोहराएँ",
   ["स्यूडोमोनास 10 ग्राम/किलो से बीज उपचार", "संक्रमित पत्तियाँ हटाएँ"],
   ["रेशा रहित, उपचारित बीज लें", "फसल अवशेष नष्ट करें", "अधिक नाइट्रोजन और जलभराव से बचें"]],
  ["कापसावरील जिवाणूजन्य करपा (कोनीय ठिपके)", "हा जिवाणूजन्य रोग बियाणे व पावसाच्या शिंतोड्यांमुळे उष्ण, दमट हवामानात पसरतो.",
   ["शिरांमध्ये कोनीय पाणथळ ठिपके जे तपकिरी-काळे होतात", "शिरांच्या बाजूने काळेपणा", "खोड व बोंडांवर काळे डाग; बोंडे सडतात"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सिक्लोराईड)", "2.5 ग्रॅम प्रति लिटर (500 ग्रॅम प्रति एकर)", "पहिली लक्षणे दिसताच फवारणी; 15 दिवसांनी पुन्हा",
   ["स्युडोमोनास 10 ग्रॅम/किलो बीजप्रक्रिया", "रोगट पाने काढा"],
   ["लिंट काढलेले, प्रक्रिया केलेले बियाणे वापरा", "पीक अवशेष नष्ट करा", "जास्त नत्र व पाणी साचणे टाळा"]])

# ---------------- MAIZE ----------------
E("maize_common_rust", "maize", "fungal", "Puccinia sorghi",
  ["rust_pustules", "brown_spots"], "ICAR-IIMR Ludhiana",
  ["Maize Common Rust", "A fungal disease spread by wind; favoured by cool (16–23 °C), humid weather.",
   ["Small cinnamon-brown powdery pustules on both sides of leaves", "Pustules turn dark later", "Leaves dry in severe cases"],
   "Mancozeb 75% WP", "2.5 g per litre (500 g per acre)", "Spray at first pustules; repeat after 10–15 days",
   ["Remove infected lower leaves", "Neem oil 5 ml/L"],
   ["Grow resistant hybrids", "Timely sowing", "Balanced nutrition"]],
  ["मक्का का रतुआ", "यह हवा से फैलने वाला फफूंद रोग है; ठंडे (16–23 °C) नम मौसम में बढ़ता है।",
   ["पत्तियों के दोनों ओर छोटे दालचीनी-भूरे पाउडर वाले फफोले", "बाद में फफोले गहरे हो जाते हैं", "गंभीर अवस्था में पत्तियाँ सूख जाती हैं"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर (500 ग्राम प्रति एकड़)", "पहले फफोले पर छिड़काव; 10–15 दिन बाद दोहराएँ",
   ["संक्रमित निचली पत्तियाँ हटाएँ", "नीम तेल 5 मि.ली./लीटर"],
   ["प्रतिरोधी संकर किस्में", "समय पर बुवाई", "संतुलित पोषण"]],
  ["मक्यावरील तांबेरा", "हा वाऱ्याने पसरणारा बुरशीजन्य रोग आहे; थंड (16–23 °C) दमट हवामानात वाढतो.",
   ["पानांच्या दोन्ही बाजूंना लहान दालचिनी-तपकिरी भुकटीचे फोड", "नंतर फोड गडद होतात", "तीव्र प्रादुर्भावात पाने वाळतात"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर (500 ग्रॅम प्रति एकर)", "पहिले फोड दिसताच फवारणी; 10–15 दिवसांनी पुन्हा",
   ["रोगट खालची पाने काढा", "निंबोळी तेल 5 मि.ली./लिटर"],
   ["प्रतिकारक संकरित वाण", "वेळेवर पेरणी", "संतुलित पोषण"]],
  [tip(["Karnataka", "Bihar", "Himachal Pradesh", "Telangana"], ["rabi"],
       "Rabi maize: rust is more common in cool months. Scout from knee-high stage.",
       "रबी मक्का: ठंडे महीनों में रतुआ अधिक होता है। घुटने की ऊँचाई की अवस्था से निगरानी करें।",
       "रब्बी मका: थंड महिन्यांत तांबेरा जास्त असतो. गुडघाभर उंचीपासून पाहणी करा.")])

E("maize_northern_leaf_blight", "maize", "fungal", "Exserohilum turcicum",
  ["leaf_blight", "long_grey_lesions", "brown_spots"], "ICAR-IIMR Ludhiana",
  ["Maize Northern (Turcicum) Leaf Blight", "A fungal disease favoured by moderate temperature (18–27 °C), heavy dew and humidity.",
   ["Long cigar-shaped grey-green to tan lesions (2–15 cm) on leaves", "Starts on lower leaves", "Leaves dry and look burnt"],
   "Mancozeb 75% WP", "2.5 g per litre (500 g per acre)", "Spray at first lesions; repeat after 10–15 days. Alternative: Propiconazole 25% EC 1 ml/L",
   ["Trichoderma seed treatment 4 g/kg", "Remove infected leaves"],
   ["Resistant hybrids", "Crop rotation; deep ploughing of residues", "Balanced fertiliser"]],
  ["मक्का का उत्तरी पत्ती झुलसा", "यह फफूंद रोग मध्यम तापमान (18–27 °C), भारी ओस और नमी में बढ़ता है।",
   ["पत्तियों पर लंबे सिगार जैसे धूसर-हरे से भूरे धब्बे (2–15 सेमी)", "निचली पत्तियों से शुरू", "पत्तियाँ सूखकर झुलसी दिखती हैं"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर (500 ग्राम प्रति एकड़)", "पहले धब्बे पर छिड़काव; 10–15 दिन बाद दोहराएँ। विकल्प: प्रोपिकोनाज़ोल 25% EC 1 मि.ली./लीटर",
   ["ट्राइकोडर्मा 4 ग्राम/किलो से बीज उपचार", "संक्रमित पत्तियाँ हटाएँ"],
   ["प्रतिरोधी संकर", "फसल चक्र; अवशेषों की गहरी जुताई", "संतुलित खाद"]],
  ["मक्यावरील उत्तरी पानांचा करपा", "हा बुरशीजन्य रोग मध्यम तापमान (18–27 °C), जास्त दव व आर्द्रतेत वाढतो.",
   ["पानांवर लांब सिगारसारखे करडे-हिरवे ते तपकिरी डाग (2–15 सेमी)", "खालच्या पानांपासून सुरुवात", "पाने वाळून करपलेली दिसतात"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर (500 ग्रॅम प्रति एकर)", "पहिले डाग दिसताच फवारणी; 10–15 दिवसांनी पुन्हा. पर्याय: प्रोपिकोनाझोल 25% EC 1 मि.ली./लिटर",
   ["ट्रायकोडर्मा 4 ग्रॅम/किलो बीजप्रक्रिया", "रोगट पाने काढा"],
   ["प्रतिकारक संकरित वाण", "फेरपालट; अवशेषांची खोल नांगरट", "संतुलित खत"]])

E("maize_gray_leaf_spot", "maize", "fungal", "Cercospora zeae-maydis",
  ["rectangular_spots", "brown_spots", "leaf_blight"], "ICAR-IIMR Ludhiana",
  ["Maize Grey Leaf Spot", "A fungal disease of warm, very humid areas; survives on maize residue left on the surface.",
   ["Rectangular grey to tan spots running parallel to leaf veins", "Spots join and kill large leaf areas", "Weak stalks"],
   "Propiconazole 25% EC", "1 ml per litre (200 ml per acre)", "Spray at first symptoms before tasseling; repeat after 15 days if needed",
   ["Remove infected leaves", "Trichoderma-enriched FYM to soil"],
   ["Rotate with legumes", "Bury crop residue", "Resistant hybrids"]],
  ["मक्का का धूसर पत्ती धब्बा", "यह गर्म, बहुत नम क्षेत्रों का फफूंद रोग है; सतह पर छोड़े गए मक्का अवशेषों पर जीवित रहता है।",
   ["पत्ती की नसों के समानांतर आयताकार धूसर-भूरे धब्बे", "धब्बे मिलकर बड़े भाग को सुखा देते हैं", "कमज़ोर तने"],
   "Propiconazole 25% EC (प्रोपिकोनाज़ोल)", "1 मि.ली. प्रति लीटर (200 मि.ली. प्रति एकड़)", "नर मंजरी से पहले पहले लक्षण पर छिड़काव; ज़रूरत हो तो 15 दिन बाद दोहराएँ",
   ["संक्रमित पत्तियाँ हटाएँ", "ट्राइकोडर्मा युक्त गोबर खाद मिट्टी में"],
   ["दलहन के साथ फसल चक्र", "फसल अवशेष दबाएँ", "प्रतिरोधी संकर"]],
  ["मक्यावरील करडे पानठिपके", "हा उष्ण, अतिदमट भागातील बुरशीजन्य रोग आहे; जमिनीवर राहिलेल्या मका अवशेषांवर टिकतो.",
   ["पानांच्या शिरांना समांतर आयताकृती करडे-तपकिरी ठिपके", "ठिपके एकत्र येऊन मोठा भाग वाळवतात", "कमकुवत खोड"],
   "Propiconazole 25% EC (प्रोपिकोनाझोल)", "1 मि.ली. प्रति लिटर (200 मि.ली. प्रति एकर)", "तुरा येण्यापूर्वी पहिली लक्षणे दिसताच फवारणी; गरज असल्यास 15 दिवसांनी पुन्हा",
   ["रोगट पाने काढा", "ट्रायकोडर्मायुक्त शेणखत जमिनीत द्या"],
   ["कडधान्यांसोबत फेरपालट", "पीक अवशेष गाडा", "प्रतिकारक संकरित वाण"]])

E("maize_fall_armyworm", "maize", "pest", "Spodoptera frugiperda",
  ["holes_chewing", "sawdust_frass", "whorl_damage"], "ICAR-IIMR / ICAR-NBAIR advisory",
  ["Maize Fall Armyworm", "An invasive caterpillar pest (since 2018 in India) that feeds inside the maize whorl and can cause heavy losses.",
   ["Ragged holes and windows on leaves", "Wet sawdust-like droppings (frass) in the whorl", "Caterpillar with inverted 'Y' mark on head"],
   "Emamectin Benzoate 5% SG", "0.4 g per litre (80 g per acre), spray into the whorl", "Spray at 5–10% plant damage; second spray after 10–15 days with Spinetoram 11.7% SC 0.5 ml/L",
   ["Put sand + lime (9:1) into whorls", "Spray neem seed kernel extract 5% or Azadirachtin 1500 ppm 5 ml/L", "Install 5 pheromone traps per acre"],
   ["Deep summer ploughing", "Timely, uniform sowing in an area", "Intercrop with pulses (tur, moong)", "Scout twice a week in first 30 days"]],
  ["मक्का का फॉल आर्मीवर्म (सैनिक कीट)", "यह आक्रामक सुंडी कीट (भारत में 2018 से) है जो मक्का की गोभ के अंदर खाती है और भारी नुकसान करती है।",
   ["पत्तियों पर फटे छेद और खिड़की जैसे निशान", "गोभ में गीले बुरादे जैसा मल", "सिर पर उल्टे 'Y' निशान वाली सुंडी"],
   "Emamectin Benzoate 5% SG (इमामेक्टिन बेंजोएट)", "0.4 ग्राम प्रति लीटर (80 ग्राम प्रति एकड़), गोभ में छिड़कें", "5–10% पौधे क्षतिग्रस्त होने पर छिड़काव; 10–15 दिन बाद स्पाइनेटोरम 11.7% SC 0.5 मि.ली./लीटर",
   ["गोभ में रेत + चूना (9:1) डालें", "नीम बीज अर्क 5% या अज़ाडिरेक्टिन 1500 ppm 5 मि.ली./लीटर छिड़कें", "प्रति एकड़ 5 फेरोमोन ट्रैप लगाएँ"],
   ["गर्मी में गहरी जुताई", "क्षेत्र में समय पर एक साथ बुवाई", "दलहन (अरहर, मूँग) के साथ अंतरफसल", "पहले 30 दिन सप्ताह में दो बार निगरानी"]],
  ["मक्यावरील लष्करी अळी (फॉल आर्मीवर्म)", "ही आक्रमक अळी (भारतात 2018 पासून) मक्याच्या पोंग्यात खाते आणि मोठे नुकसान करते.",
   ["पानांवर फाटलेली छिद्रे व खिडक्यांसारखे डाग", "पोंग्यात ओल्या भुशासारखी विष्ठा", "डोक्यावर उलटा 'Y' खूण असलेली अळी"],
   "Emamectin Benzoate 5% SG (इमामेक्टिन बेंझोएट)", "0.4 ग्रॅम प्रति लिटर (80 ग्रॅम प्रति एकर), पोंग्यात फवारा", "5–10% झाडांचे नुकसान दिसताच फवारणी; 10–15 दिवसांनी स्पिनेटोरम 11.7% SC 0.5 मि.ली./लिटर",
   ["पोंग्यात वाळू + चुना (9:1) टाका", "निंबोळी अर्क 5% किंवा अझाडिरॅक्टिन 1500 ppm 5 मि.ली./लिटर फवारा", "एकरी 5 कामगंध सापळे लावा"],
   ["उन्हाळ्यात खोल नांगरट", "परिसरात वेळेवर एकाच वेळी पेरणी", "कडधान्यांसोबत (तूर, मूग) आंतरपीक", "पहिले 30 दिवस आठवड्यातून दोनदा पाहणी"]],
  [tip(["Karnataka", "Maharashtra", "Telangana", "Andhra Pradesh", "Tamil Nadu", "Madhya Pradesh"], ["kharif"],
       "Kharif maize in peninsular India sees peak armyworm attack 15–40 days after sowing. Start scouting from day 7.",
       "प्रायद्वीपीय भारत में खरीफ मक्का में बुवाई के 15–40 दिन बाद आर्मीवर्म का अधिक प्रकोप होता है। 7वें दिन से निगरानी शुरू करें।",
       "द्वीपकल्पीय भारतात खरीप मक्यात पेरणीनंतर 15–40 दिवसांत लष्करी अळीचा प्रादुर्भाव जास्त असतो. 7व्या दिवसापासून पाहणी सुरू करा.")])

# ---------------- CHILLI / PEPPER ----------------
E("chilli_anthracnose", "chilli", "fungal", "Colletotrichum capsici",
  ["sunken_fruit_spots", "fruit_rot", "dieback", "black_spots"], "ICAR-IIHR / Dr. YSR Horticultural University",
  ["Chilli Anthracnose (Fruit Rot & Dieback)", "A fungal disease (Colletotrichum) spread by infected seed and rain splash; serious in warm, humid weather.",
   ["Sunken, circular dark spots with rings on ripe fruits", "Fruits shrivel and turn straw coloured", "Twigs dry from the tip downward (dieback)"],
   "Propiconazole 25% EC", "1 ml per litre (200 ml per acre)", "Spray at flowering and at fruit-setting; repeat after 15 days. Alternative: Azoxystrobin 23% SC 1 ml/L",
   ["Seed treatment with Trichoderma 4 g/kg", "Spray Pseudomonas fluorescens 10 g/L", "Pick and destroy infected fruits"],
   ["Use disease-free seed from healthy fruits", "Prune and burn dried twigs", "Avoid water stagnation", "Crop rotation with non-solanaceous crops"]],
  ["मिर्च का एन्थ्रेक्नोज (फल सड़न व शीर्ष मरण)", "यह फफूंद रोग संक्रमित बीज और बारिश की छींटों से फैलता है; गर्म, नम मौसम में गंभीर।",
   ["पके फलों पर छल्लों वाले धँसे, गोल काले धब्बे", "फल सिकुड़कर भूसे के रंग के हो जाते हैं", "टहनियाँ सिरे से नीचे की ओर सूखती हैं"],
   "Propiconazole 25% EC (प्रोपिकोनाज़ोल)", "1 मि.ली. प्रति लीटर (200 मि.ली. प्रति एकड़)", "फूल आने और फल बनने पर छिड़काव; 15 दिन बाद दोहराएँ। विकल्प: एज़ोक्सीस्ट्रोबिन 23% SC 1 मि.ली./लीटर",
   ["ट्राइकोडर्मा 4 ग्राम/किलो से बीज उपचार", "स्यूडोमोनास 10 ग्राम/लीटर छिड़कें", "संक्रमित फल तोड़कर नष्ट करें"],
   ["स्वस्थ फलों से रोगमुक्त बीज लें", "सूखी टहनियाँ काटकर जलाएँ", "पानी जमा न होने दें", "फसल चक्र अपनाएँ"]],
  ["मिरचीवरील करपा (फळकूज व फांदीमर)", "हा बुरशीजन्य रोग रोगट बियाणे व पावसाच्या शिंतोड्यांनी पसरतो; उष्ण, दमट हवामानात गंभीर.",
   ["पिकलेल्या फळांवर कड्यांचे खोलगट, गोल काळे डाग", "फळे आकसून गवताच्या रंगाची होतात", "फांद्या टोकाकडून खाली वाळतात"],
   "Propiconazole 25% EC (प्रोपिकोनाझोल)", "1 मि.ली. प्रति लिटर (200 मि.ली. प्रति एकर)", "फुलोरा व फळधारणेवेळी फवारणी; 15 दिवसांनी पुन्हा. पर्याय: ॲझोक्सिस्ट्रोबिन 23% SC 1 मि.ली./लिटर",
   ["ट्रायकोडर्मा 4 ग्रॅम/किलो बीजप्रक्रिया", "स्युडोमोनास 10 ग्रॅम/लिटर फवारा", "रोगट फळे तोडून नष्ट करा"],
   ["निरोगी फळांपासून रोगमुक्त बियाणे वापरा", "वाळलेल्या फांद्या छाटून जाळा", "पाणी साचू देऊ नका", "फेरपालट करा"]],
  [tip(["Andhra Pradesh", "Telangana", "Karnataka", "Maharashtra"], ["kharif", "rabi"],
       "Major chilli belts (Guntur, Byadgi, Nandurbar): anthracnose peaks after Sept–Oct rains; protect at red-fruit stage.",
       "प्रमुख मिर्च क्षेत्र (गुंटूर, ब्याडगी, नंदुरबार): सितंबर–अक्टूबर की बारिश के बाद एन्थ्रेक्नोज अधिक होता है; लाल फल अवस्था में बचाव करें।",
       "प्रमुख मिरची पट्टे (गुंटूर, ब्याडगी, नंदुरबार): सप्टेंबर–ऑक्टोबर पावसानंतर करपा वाढतो; लाल फळ अवस्थेत संरक्षण करा.")])

E("chilli_leaf_curl", "chilli", "viral", "Chilli leaf curl virus (whitefly) + thrips/mites",
  ["leaf_curl", "small_leaves", "stunted", "insects_underside", "yellowing"], "ICAR-IIHR / ICAR-IIVR",
  ["Chilli Leaf Curl (Murda complex)", "Caused by a whitefly-transmitted virus, often together with thrips and mites that make leaves curl. Very common in chilli.",
   ["Leaves curl upward (virus/thrips) or downward (mites), small and puckered", "Bushy, stunted plants", "Flower and fruit drop"],
   "Fipronil 5% SC (thrips) / Imidacloprid 17.8% SL (whitefly)", "Fipronil 2 ml/L or Imidacloprid 0.3 ml/L (one at a time, never mixed)", "Spray when insects are seen; repeat after 15 days rotating chemical groups. For mites: Spiromesifen 22.9% SC 0.8 ml/L",
   ["Yellow & blue sticky traps 10 per acre", "Neem oil 5 ml/L every 10 days", "Border crop of maize/sorghum (2 rows)"],
   ["Nursery under insect-proof net", "Uproot virus-infected plants early", "Avoid planting chilli near old infected fields or tomato", "Balanced fertiliser, avoid excess nitrogen"]],
  ["मिर्च का पत्ती मरोड़ (मुर्दा रोग)", "सफेद मक्खी से फैलने वाले विषाणु से होता है, अक्सर थ्रिप्स और माइट के साथ जो पत्तियाँ मोड़ते हैं। मिर्च में बहुत आम।",
   ["पत्तियाँ ऊपर (विषाणु/थ्रिप्स) या नीचे (माइट) मुड़ती हैं, छोटी व सिकुड़ी", "झाड़ीनुमा, बौने पौधे", "फूल और फल झड़ते हैं"],
   "Fipronil 5% SC (थ्रिप्स) / Imidacloprid 17.8% SL (सफेद मक्खी)", "फिप्रोनिल 2 मि.ली./लीटर या इमिडाक्लोप्रिड 0.3 मि.ली./लीटर (एक बार में एक, कभी न मिलाएँ)", "कीट दिखने पर छिड़काव; 15 दिन बाद दवा बदलकर दोहराएँ। माइट हेतु: स्पाइरोमेसिफेन 22.9% SC 0.8 मि.ली./लीटर",
   ["प्रति एकड़ 10 पीले व नीले चिपचिपे ट्रैप", "हर 10 दिन पर नीम तेल 5 मि.ली./लीटर", "किनारे पर मक्का/ज्वार की 2 कतारें"],
   ["कीटरोधी जाली में नर्सरी", "विषाणु ग्रस्त पौधे जल्दी उखाड़ें", "पुराने संक्रमित खेत या टमाटर के पास मिर्च न लगाएँ", "संतुलित खाद, अधिक नाइट्रोजन नहीं"]],
  ["मिरचीवरील चुरडा-मुरडा (पर्णगुच्छ)", "पांढऱ्या माशीमुळे पसरणाऱ्या विषाणूमुळे होतो, अनेकदा फुलकिडे व कोळी यांच्यासोबत जे पाने वळवतात. मिरचीत अतिशय सामान्य.",
   ["पाने वर (विषाणू/फुलकिडे) किंवा खाली (कोळी) वळतात, लहान व सुरकुतलेली", "झुडपासारखी, खुजी झाडे", "फुले व फळे गळतात"],
   "Fipronil 5% SC (फुलकिडे) / Imidacloprid 17.8% SL (पांढरी माशी)", "फिप्रोनिल 2 मि.ली./लिटर किंवा इमिडाक्लोप्रिड 0.3 मि.ली./लिटर (एका वेळी एकच, कधीही मिसळू नका)", "कीड दिसताच फवारणी; 15 दिवसांनी औषध बदलून पुन्हा. कोळ्यासाठी: स्पायरोमेसिफेन 22.9% SC 0.8 मि.ली./लिटर",
   ["एकरी 10 पिवळे व निळे चिकट सापळे", "दर 10 दिवसांनी निंबोळी तेल 5 मि.ली./लिटर", "कडेने मका/ज्वारीच्या 2 ओळी"],
   ["कीटकरोधी जाळीत रोपवाटिका", "विषाणूग्रस्त झाडे लवकर उपटा", "जुन्या रोगट शेताजवळ किंवा टोमॅटोजवळ मिरची लावू नका", "संतुलित खत, जास्त नत्र टाळा"]])

E("pepper_bacterial_spot", "chilli", "bacterial", "Xanthomonas euvesicatoria",
  ["water_soaked", "brown_spots", "yellowing", "fruit_spots"], ICAR,
  ["Chilli / Capsicum Bacterial Leaf Spot", "A bacterial disease spread by infected seed and rain splash in warm, wet weather.",
   ["Small water-soaked spots turning brown with yellow halo", "Leaves turn yellow and drop", "Raised, scabby spots on fruits"],
   "Copper Oxychloride 50% WP", "3 g per litre (600 g per acre)", "Spray at first symptoms; repeat every 10 days during rains (max 3)",
   ["Seed treatment with Pseudomonas fluorescens 10 g/kg", "Spray Pseudomonas 10 g/L"],
   ["Disease-free seed", "Avoid overhead irrigation", "Rotate with non-solanaceous crops"]],
  ["मिर्च / शिमला मिर्च का जीवाणु पत्ती धब्बा", "यह जीवाणु रोग संक्रमित बीज और बारिश की छींटों से गर्म, गीले मौसम में फैलता है।",
   ["छोटे पानी जैसे धब्बे जो पीले घेरे के साथ भूरे होते हैं", "पत्तियाँ पीली होकर गिरती हैं", "फलों पर उभरे खुरदरे धब्बे"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सीक्लोराइड)", "3 ग्राम प्रति लीटर (600 ग्राम प्रति एकड़)", "पहले लक्षण पर छिड़काव; बारिश में हर 10 दिन पर (अधिकतम 3)",
   ["स्यूडोमोनास 10 ग्राम/किलो से बीज उपचार", "स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["रोगमुक्त बीज", "ऊपर से सिंचाई न करें", "फसल चक्र अपनाएँ"]],
  ["मिरची / ढोबळी मिरचीवरील जिवाणूजन्य ठिपके", "हा जिवाणूजन्य रोग रोगट बियाणे व पावसाच्या शिंतोड्यांनी उष्ण, ओल्या हवामानात पसरतो.",
   ["लहान पाणथळ ठिपके जे पिवळ्या कड्यासह तपकिरी होतात", "पाने पिवळी पडून गळतात", "फळांवर उंचवटलेले खडबडीत डाग"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सिक्लोराईड)", "3 ग्रॅम प्रति लिटर (600 ग्रॅम प्रति एकर)", "पहिली लक्षणे दिसताच फवारणी; पावसाळ्यात दर 10 दिवसांनी (जास्तीत जास्त 3)",
   ["स्युडोमोनास 10 ग्रॅम/किलो बीजप्रक्रिया", "स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["रोगमुक्त बियाणे", "तुषार सिंचन टाळा", "फेरपालट करा"]])

# ---------------- FRUIT & OTHER PLANTVILLAGE CROPS (compact) ----------------
def F(id, crop, kind, pathogen, tags, en, hi, mr):
    E(id, crop, kind, pathogen, tags, "ICAR / State Agricultural University (horticulture) guideline", en, hi, mr)


F("apple_scab", "apple", "fungal", "Venturia inaequalis", ["olive_spots", "black_spots", "fruit_spots"],
  ["Apple Scab", "A fungal disease of cool, wet spring weather; survives in fallen leaves.", ["Olive-green to black velvety spots on leaves", "Dark, cracked scabby spots on fruits"],
   "Mancozeb 75% WP", "3 g per litre", "From green-tip stage, every 10–14 days in wet weather as per SKUAST/YSPUHF spray schedule", ["Collect and destroy fallen leaves", "Spray 5% urea on fallen leaves in autumn to rot them"], ["Prune for open canopy", "Grow scab-resistant varieties"]],
  ["सेब का स्कैब (पपड़ी रोग)", "ठंडे, गीले वसंत मौसम का फफूंद रोग; गिरी पत्तियों में जीवित रहता है।", ["पत्तियों पर जैतूनी-हरे से काले मखमली धब्बे", "फलों पर गहरे, फटे पपड़ीदार धब्बे"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "3 ग्राम प्रति लीटर", "हरी कली अवस्था से, गीले मौसम में हर 10–14 दिन पर विश्वविद्यालय की स्प्रे सारणी अनुसार", ["गिरी पत्तियाँ इकट्ठा कर नष्ट करें", "पतझड़ में गिरी पत्तियों पर 5% यूरिया छिड़कें"], ["खुली छतरी हेतु छँटाई", "स्कैब प्रतिरोधी किस्में"]],
  ["सफरचंदावरील खरूज (स्कॅब)", "थंड, ओल्या वसंत हवामानातील बुरशीजन्य रोग; गळालेल्या पानांत टिकतो.", ["पानांवर ऑलिव्ह-हिरवे ते काळे मखमली ठिपके", "फळांवर गडद, तडकलेले खरूजासारखे डाग"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "3 ग्रॅम प्रति लिटर", "हिरव्या कळी अवस्थेपासून, ओल्या हवामानात दर 10–14 दिवसांनी विद्यापीठ वेळापत्रकाप्रमाणे", ["गळालेली पाने गोळा करून नष्ट करा", "शरद ऋतूत गळालेल्या पानांवर 5% युरिया फवारा"], ["मोकळ्या छत्रीसाठी छाटणी", "प्रतिकारक जाती"]])

F("apple_black_rot", "apple", "fungal", "Botryosphaeria obtusa", ["brown_spots", "concentric_rings", "fruit_rot", "cankers"],
  ["Apple Black Rot", "A fungal disease that enters through wounds and survives in dead wood and mummified fruits.", ["Purple-edged 'frog-eye' spots on leaves", "Black rotting area on fruit with rings", "Sunken cankers on branches"],
   "Captan 50% WP", "2.5 g per litre", "Spray from petal fall every 10–14 days in wet weather", ["Remove mummified fruits and dead wood", "Paint pruning cuts with Bordeaux paste"], ["Prune out cankers in winter", "Avoid tree injuries"]],
  ["सेब का काला सड़न", "घावों से प्रवेश करने वाला फफूंद रोग; मृत लकड़ी और सूखे फलों में जीवित रहता है।", ["पत्तियों पर बैंगनी किनारे वाले 'मेंढक-आँख' धब्बे", "फल पर छल्लों वाला काला सड़ा भाग", "शाखाओं पर धँसे कैंकर"],
   "Captan 50% WP (कैप्टान)", "2.5 ग्राम प्रति लीटर", "पंखुड़ी गिरने से गीले मौसम में हर 10–14 दिन पर", ["सूखे फल और मृत लकड़ी हटाएँ", "छँटाई के घावों पर बोर्डो पेस्ट लगाएँ"], ["सर्दी में कैंकर काटें", "पेड़ों को चोट से बचाएँ"]],
  ["सफरचंदावरील काळी कूज", "जखमांतून शिरणारा बुरशीजन्य रोग; मृत लाकूड व सुकलेल्या फळांत टिकतो.", ["पानांवर जांभळ्या कडेचे 'बेडूक-डोळा' ठिपके", "फळावर कड्यांचा काळा कुजलेला भाग", "फांद्यांवर खोलगट कँकर"],
   "Captan 50% WP (कॅप्टान)", "2.5 ग्रॅम प्रति लिटर", "पाकळ्या गळाल्यापासून ओल्या हवामानात दर 10–14 दिवसांनी", ["सुकलेली फळे व मृत लाकूड काढा", "छाटणीच्या जखमांवर बोर्डो पेस्ट लावा"], ["हिवाळ्यात कँकर छाटा", "झाडांना इजा टाळा"]])

F("apple_cedar_rust", "apple", "fungal", "Gymnosporangium juniperi-virginianae", ["yellow_spots", "rust_pustules"],
  ["Apple Cedar Rust", "A rust fungus that needs juniper/cedar trees nearby to complete its life cycle.", ["Bright yellow-orange spots on upper leaf surface", "Small tube-like growths under spots"],
   "Mancozeb 75% WP", "3 g per litre", "Spray from pink-bud to petal fall, every 7–10 days in wet spring", ["Remove nearby juniper/cedar hosts where possible"], ["Plant resistant varieties", "Keep orchards away from juniper"]],
  ["सेब का सीडर रतुआ", "यह रतुआ फफूंद अपना जीवन चक्र पूरा करने के लिए पास के जुनिपर/देवदार पेड़ों पर निर्भर है।", ["पत्ती की ऊपरी सतह पर चमकीले पीले-नारंगी धब्बे", "धब्बों के नीचे छोटी नली जैसी संरचनाएँ"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "3 ग्राम प्रति लीटर", "गुलाबी कली से पंखुड़ी गिरने तक, गीले वसंत में हर 7–10 दिन पर", ["संभव हो तो पास के जुनिपर पेड़ हटाएँ"], ["प्रतिरोधी किस्में", "बाग जुनिपर से दूर रखें"]],
  ["सफरचंदावरील सीडर तांबेरा", "हा तांबेरा बुरशी जीवनचक्र पूर्ण करण्यासाठी जवळच्या ज्युनिपर/देवदार झाडांवर अवलंबून असते.", ["पानाच्या वरच्या बाजूस चमकदार पिवळे-नारिंगी ठिपके", "ठिपक्यांखाली लहान नळीसारखी वाढ"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "3 ग्रॅम प्रति लिटर", "गुलाबी कळी ते पाकळ्या गळेपर्यंत, ओल्या वसंतात दर 7–10 दिवसांनी", ["शक्य असल्यास जवळची ज्युनिपर झाडे काढा"], ["प्रतिकारक जाती", "बाग ज्युनिपरपासून दूर ठेवा"]])

F("cherry_powdery_mildew", "cherry", "fungal", "Podosphaera clandestina", ["white_powder", "leaf_curl"],
  ["Cherry Powdery Mildew", "A fungal disease of warm days and cool humid nights.", ["White powdery patches on young leaves", "Leaves curl and become distorted"],
   "Hexaconazole 5% EC", "1 ml per litre", "Spray at first patches; repeat after 10–15 days", ["Wettable sulphur 80% WP 2 g/L (not in very hot weather)"], ["Prune for air flow", "Avoid excess nitrogen"]],
  ["चेरी का चूर्णिल आसिता", "गर्म दिन और ठंडी नम रातों का फफूंद रोग।", ["नई पत्तियों पर सफेद पाउडर जैसे धब्बे", "पत्तियाँ मुड़कर विकृत होती हैं"],
   "Hexaconazole 5% EC (हेक्साकोनाज़ोल)", "1 मि.ली. प्रति लीटर", "पहले धब्बे पर छिड़काव; 10–15 दिन बाद दोहराएँ", ["घुलनशील गंधक 80% WP 2 ग्राम/लीटर (बहुत गर्मी में नहीं)"], ["हवा हेतु छँटाई", "अधिक नाइट्रोजन न दें"]],
  ["चेरीवरील भुरी", "उष्ण दिवस व थंड दमट रात्रींचा बुरशीजन्य रोग.", ["कोवळ्या पानांवर पांढरे भुकटीसारखे चट्टे", "पाने वळून वेडीवाकडी होतात"],
   "Hexaconazole 5% EC (हेक्झाकोनाझोल)", "1 मि.ली. प्रति लिटर", "पहिले चट्टे दिसताच फवारणी; 10–15 दिवसांनी पुन्हा", ["पाण्यात मिसळणारे गंधक 80% WP 2 ग्रॅम/लिटर (कडक उन्हात नाही)"], ["हवेसाठी छाटणी", "जास्त नत्र टाळा"]])

F("grape_black_rot", "grape", "fungal", "Guignardia bidwellii", ["brown_spots", "black_spots", "fruit_rot"],
  ["Grape Black Rot", "A fungal disease of warm, wet weather; survives in mummified berries.", ["Reddish-brown spots with dark border on leaves", "Berries turn black, shrivel into hard mummies"],
   "Mancozeb 75% WP", "2 g per litre", "Spray from new shoot growth till berry set, every 10–14 days in rain", ["Remove mummified berries and infected canes"], ["Open canopy by pruning", "Clean vineyard floor"]],
  ["अंगूर का काला सड़न", "गर्म, गीले मौसम का फफूंद रोग; सूखे दानों में जीवित रहता है।", ["पत्तियों पर गहरे किनारे वाले लाल-भूरे धब्बे", "दाने काले होकर सिकुड़ते और सख्त हो जाते हैं"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2 ग्राम प्रति लीटर", "नई टहनी से दाने बनने तक, बारिश में हर 10–14 दिन पर", ["सूखे दाने और संक्रमित बेलें हटाएँ"], ["छँटाई से खुली छतरी", "बाग की ज़मीन साफ रखें"]],
  ["द्राक्षावरील काळी कूज", "उष्ण, ओल्या हवामानातील बुरशीजन्य रोग; सुकलेल्या मण्यांत टिकतो.", ["पानांवर गडद कडेचे लालसर-तपकिरी ठिपके", "मणी काळे होऊन आकसतात व कडक होतात"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2 ग्रॅम प्रति लिटर", "नवीन फुटीपासून मणी धरेपर्यंत, पावसात दर 10–14 दिवसांनी", ["सुकलेले मणी व रोगट काड्या काढा"], ["छाटणीने मोकळी छत्री", "बागेतील जमीन स्वच्छ ठेवा"]])

F("grape_esca", "grape", "fungal", "Phaeomoniella / Phaeoacremonium (trunk disease)", ["tiger_stripes", "brown_spots", "wilting", "dieback"],
  ["Grape Esca (Black Measles)", "A wood-decay disease entering through pruning wounds. No chemical cure once inside the trunk.", ["Tiger-stripe yellow/red patterns between leaf veins", "Dark spots on berries", "Sudden wilting of vine (apoplexy)"],
   "No curative chemical – protect pruning wounds", "Apply Carbendazim 50% WP paste (10 g in 100 ml water) on large cuts", "Immediately after each pruning", ["Paint cuts with Trichoderma paste", "Remove and burn badly infected wood"], ["Prune in dry weather", "Use healthy planting material"]],
  ["अंगूर का एस्का (काला खसरा)", "छँटाई के घावों से प्रवेश करने वाला लकड़ी सड़न रोग। तने में पहुँचने के बाद कोई रासायनिक इलाज नहीं।", ["पत्ती की नसों के बीच बाघ-धारी जैसे पीले/लाल निशान", "दानों पर गहरे धब्बे", "बेल का अचानक मुरझाना"],
   "कोई उपचारक रसायन नहीं – छँटाई के घाव बचाएँ", "बड़े कटों पर कार्बेन्डाज़िम 50% WP का लेप (10 ग्राम 100 मि.ली. पानी में)", "हर छँटाई के तुरंत बाद", ["कटों पर ट्राइकोडर्मा लेप लगाएँ", "बुरी तरह संक्रमित लकड़ी हटाकर जलाएँ"], ["सूखे मौसम में छँटाई", "स्वस्थ रोपण सामग्री"]],
  ["द्राक्षावरील एस्का (ब्लॅक मीझल्स)", "छाटणीच्या जखमांतून शिरणारा लाकूड कुजवणारा रोग. खोडात शिरल्यानंतर रासायनिक उपाय नाही.", ["पानांच्या शिरांमध्ये वाघाच्या पट्ट्यांसारखे पिवळे/लाल पट्टे", "मण्यांवर गडद ठिपके", "वेल अचानक मलूल होणे"],
   "उपचारक रसायन नाही – छाटणीच्या जखमा संरक्षित करा", "मोठ्या कापांवर कार्बेन्डाझिम 50% WP लेप (10 ग्रॅम 100 मि.ली. पाण्यात)", "प्रत्येक छाटणीनंतर लगेच", ["कापांवर ट्रायकोडर्मा लेप लावा", "जास्त रोगट लाकूड काढून जाळा"], ["कोरड्या हवामानात छाटणी", "निरोगी लागवड साहित्य"]])

F("grape_leaf_blight", "grape", "fungal", "Pseudocercospora vitis (Isariopsis)", ["brown_spots", "leaf_blight", "yellowing"],
  ["Grape Leaf Blight (Isariopsis Leaf Spot)", "A fungal leaf spot common late in the season in humid weather.", ["Irregular dark-brown spots on leaves", "Leaves dry and fall early"],
   "Copper Oxychloride 50% WP", "3 g per litre", "Spray at first spots; repeat after 15 days", ["Remove infected leaves", "Bordeaux mixture 1%"], ["Good air flow", "Balanced nutrition"]],
  ["अंगूर का पत्ती झुलसा", "नम मौसम में मौसम के अंत में होने वाला फफूंद पत्ती धब्बा।", ["पत्तियों पर अनियमित गहरे भूरे धब्बे", "पत्तियाँ जल्दी सूखकर गिरती हैं"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सीक्लोराइड)", "3 ग्राम प्रति लीटर", "पहले धब्बे पर छिड़काव; 15 दिन बाद दोहराएँ", ["संक्रमित पत्तियाँ हटाएँ", "1% बोर्डो मिश्रण"], ["अच्छा वायु संचार", "संतुलित पोषण"]],
  ["द्राक्षावरील पानांचा करपा", "दमट हवामानात हंगामाच्या शेवटी येणारा बुरशीजन्य पानठिपका.", ["पानांवर अनियमित गडद तपकिरी ठिपके", "पाने लवकर वाळून गळतात"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सिक्लोराईड)", "3 ग्रॅम प्रति लिटर", "पहिले ठिपके दिसताच फवारणी; 15 दिवसांनी पुन्हा", ["रोगट पाने काढा", "1% बोर्डो मिश्रण"], ["हवा खेळती ठेवा", "संतुलित पोषण"]])

F("orange_citrus_greening", "orange", "bacterial", "Candidatus Liberibacter (spread by citrus psyllid)", ["yellowing", "blotchy_mottle", "small_leaves", "fruit_misshapen"],
  ["Citrus Greening (Huanglongbing)", "A bacterial disease spread by the citrus psyllid insect. No cure – infected trees decline and die.", ["Blotchy, uneven yellowing of leaves (not symmetric)", "Small, lopsided, bitter fruits that stay green", "Twig dieback"],
   "Imidacloprid 17.8% SL (for psyllid)", "0.3 ml per litre", "Spray at each new flush when psyllids are seen", ["Neem oil 5 ml/L on new flushes", "Remove and destroy infected trees"], ["Plant certified disease-free nursery plants", "Control psyllid in the whole area", "Balanced nutrition with zinc"]],
  ["नींबू वर्गीय ग्रीनिंग (हुआंगलोंगबिंग)", "सिट्रस सिल्ला कीट से फैलने वाला जीवाणु रोग। कोई इलाज नहीं – संक्रमित पेड़ कमज़ोर होकर मर जाते हैं।", ["पत्तियों का असमान, धब्बेदार पीलापन", "छोटे, टेढ़े, कड़वे फल जो हरे रहते हैं", "टहनियाँ सूखती हैं"],
   "Imidacloprid 17.8% SL (इमिडाक्लोप्रिड - सिल्ला हेतु)", "0.3 मि.ली. प्रति लीटर", "हर नई पत्तियों के निकलने पर सिल्ला दिखने पर छिड़काव", ["नई पत्तियों पर नीम तेल 5 मि.ली./लीटर", "संक्रमित पेड़ हटाकर नष्ट करें"], ["प्रमाणित रोगमुक्त नर्सरी पौधे", "पूरे क्षेत्र में सिल्ला नियंत्रण", "ज़िंक सहित संतुलित पोषण"]],
  ["लिंबूवर्गीय ग्रीनिंग (हुआंगलाँगबिंग)", "सिट्रस सायला किडीमुळे पसरणारा जिवाणूजन्य रोग. उपाय नाही – रोगट झाडे खंगून मरतात.", ["पानांचा असमान, चट्टेदार पिवळेपणा", "लहान, वाकडी, कडू फळे जी हिरवी राहतात", "फांद्या वाळतात"],
   "Imidacloprid 17.8% SL (इमिडाक्लोप्रिड - सायलासाठी)", "0.3 मि.ली. प्रति लिटर", "प्रत्येक नवीन नवतीवर सायला दिसताच फवारणी", ["नवतीवर निंबोळी तेल 5 मि.ली./लिटर", "रोगट झाडे काढून नष्ट करा"], ["प्रमाणित रोगमुक्त रोपे", "संपूर्ण परिसरात सायला नियंत्रण", "झिंकसह संतुलित पोषण"]])

F("peach_bacterial_spot", "peach", "bacterial", "Xanthomonas arboricola pv. pruni", ["water_soaked", "shot_holes", "fruit_spots"],
  ["Peach Bacterial Spot", "A bacterial disease spread by rain and wind in warm, wet weather.", ["Small angular purple-brown spots that fall out leaving holes", "Sunken cracked spots on fruits"],
   "Copper Oxychloride 50% WP", "3 g per litre", "Spray at leaf fall and before bud break; during season at lower dose as per label", ["Remove infected twigs"], ["Resistant varieties", "Windbreaks", "Balanced nitrogen"]],
  ["आड़ू का जीवाणु धब्बा", "गर्म, गीले मौसम में बारिश और हवा से फैलने वाला जीवाणु रोग।", ["छोटे कोणीय बैंगनी-भूरे धब्बे जो गिरकर छेद छोड़ते हैं", "फलों पर धँसे फटे धब्बे"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सीक्लोराइड)", "3 ग्राम प्रति लीटर", "पत्ती गिरने पर और कली फूटने से पहले छिड़काव", ["संक्रमित टहनियाँ हटाएँ"], ["प्रतिरोधी किस्में", "वायु अवरोधक पेड़", "संतुलित नाइट्रोजन"]],
  ["पीचवरील जिवाणूजन्य ठिपके", "उष्ण, ओल्या हवामानात पाऊस व वाऱ्याने पसरणारा जिवाणूजन्य रोग.", ["लहान कोनीय जांभळट-तपकिरी ठिपके जे गळून छिद्रे राहतात", "फळांवर खोलगट तडकलेले डाग"],
   "Copper Oxychloride 50% WP (कॉपर ऑक्सिक्लोराईड)", "3 ग्रॅम प्रति लिटर", "पानगळीवेळी व कळी फुटण्यापूर्वी फवारणी", ["रोगट फांद्या काढा"], ["प्रतिकारक जाती", "वारारोधक झाडे", "संतुलित नत्र"]])

F("squash_powdery_mildew", "squash", "fungal", "Podosphaera xanthii", ["white_powder", "yellowing"],
  ["Cucurbit Powdery Mildew", "A fungal disease of pumpkin, squash and other gourds; common in dry days with humid nights.", ["White powdery spots on both leaf surfaces", "Leaves turn yellow, brown and dry"],
   "Hexaconazole 5% EC", "1 ml per litre", "Spray at first spots; repeat after 10–15 days", ["Wettable sulphur 80% WP 2 g/L", "Spray 10% milk solution"], ["Resistant varieties", "Adequate spacing", "Remove old infected vines"]],
  ["कद्दू वर्गीय चूर्णिल आसिता", "कद्दू, तोरी और अन्य बेल वाली फसलों का फफूंद रोग; सूखे दिन और नम रातों में आम।", ["पत्ती की दोनों सतहों पर सफेद पाउडर जैसे धब्बे", "पत्तियाँ पीली, भूरी होकर सूखती हैं"],
   "Hexaconazole 5% EC (हेक्साकोनाज़ोल)", "1 मि.ली. प्रति लीटर", "पहले धब्बे पर छिड़काव; 10–15 दिन बाद दोहराएँ", ["घुलनशील गंधक 80% WP 2 ग्राम/लीटर", "10% दूध का घोल छिड़कें"], ["प्रतिरोधी किस्में", "उचित दूरी", "पुरानी संक्रमित बेलें हटाएँ"]],
  ["वेलवर्गीय पिकांवरील भुरी", "भोपळा, दोडका व इतर वेलवर्गीय पिकांचा बुरशीजन्य रोग; कोरडे दिवस व दमट रात्रींत सामान्य.", ["पानांच्या दोन्ही बाजूंना पांढरे भुकटीसारखे ठिपके", "पाने पिवळी, तपकिरी होऊन वाळतात"],
   "Hexaconazole 5% EC (हेक्झाकोनाझोल)", "1 मि.ली. प्रति लिटर", "पहिले ठिपके दिसताच फवारणी; 10–15 दिवसांनी पुन्हा", ["पाण्यात मिसळणारे गंधक 80% WP 2 ग्रॅम/लिटर", "10% दुधाचे द्रावण फवारा"], ["प्रतिकारक जाती", "योग्य अंतर", "जुने रोगट वेल काढा"]])

F("strawberry_leaf_scorch", "strawberry", "fungal", "Diplocarpon earlianum", ["purple_spots", "leaf_blight"],
  ["Strawberry Leaf Scorch", "A fungal disease spread by water splash in warm, wet weather.", ["Many small purple spots on leaves", "Spots join, leaves look burnt and dry"],
   "Captan 50% WP", "2 g per litre", "Spray at first spots; repeat after 10–14 days", ["Remove old infected leaves after harvest"], ["Use drip irrigation and mulch", "Healthy runners", "Renovate beds yearly"]],
  ["स्ट्रॉबेरी का पत्ती झुलसा", "गर्म, गीले मौसम में पानी की छींटों से फैलने वाला फफूंद रोग।", ["पत्तियों पर कई छोटे बैंगनी धब्बे", "धब्बे मिलकर पत्तियाँ झुलसी व सूखी दिखती हैं"],
   "Captan 50% WP (कैप्टान)", "2 ग्राम प्रति लीटर", "पहले धब्बे पर छिड़काव; 10–14 दिन बाद दोहराएँ", ["कटाई के बाद पुरानी संक्रमित पत्तियाँ हटाएँ"], ["ड्रिप सिंचाई और मल्चिंग", "स्वस्थ रनर", "हर साल क्यारियाँ नवीनीकरण"]],
  ["स्ट्रॉबेरीवरील पानांचा करपा", "उष्ण, ओल्या हवामानात पाण्याच्या शिंतोड्यांनी पसरणारा बुरशीजन्य रोग.", ["पानांवर अनेक लहान जांभळे ठिपके", "ठिपके एकत्र येऊन पाने करपलेली व वाळलेली दिसतात"],
   "Captan 50% WP (कॅप्टान)", "2 ग्रॅम प्रति लिटर", "पहिले ठिपके दिसताच फवारणी; 10–14 दिवसांनी पुन्हा", ["काढणीनंतर जुनी रोगट पाने काढा"], ["ठिबक सिंचन व आच्छादन", "निरोगी रनर", "दरवर्षी वाफे नूतनीकरण"]])

# ---------------- NEW: RICE / WHEAT / COTTON (photo-detectable) ----------------
E("rice_tungro", "rice", "viral", "Rice tungro viruses (spread by green leafhopper)",
  ["yellowing", "stunted", "insects_underside"], "ICAR-NRRI Cuttack / ICAR-IIRR Hyderabad",
  ["Rice Tungro Virus", "A virus disease spread by the green leafhopper insect. Infected plants cannot be cured; control the leafhopper and remove infected plants early.",
   ["Leaves turn yellow-orange starting from the tip", "Plants are stunted with fewer tillers", "Young leaves twist; panicles are small and grains partly empty"],
   "Thiamethoxam 25% WG (for green leafhopper)", "0.2 g per litre (40 g per acre in 200 L water)", "Spray in nursery and 15 and 30 days after transplanting when leafhoppers are seen; alternate with Imidacloprid 17.8% SL 0.25 ml/L",
   ["Install light traps to monitor and kill leafhoppers", "Uproot and bury infected hills", "Neem oil (1500 ppm) 5 ml/L in nursery"],
   ["Grow tungro-resistant varieties recommended for your state", "Synchronous planting in the whole village", "Remove stubble and volunteer rice after harvest", "Avoid planting near infected fields"]],
  ["धान का टुंग्रो विषाणु रोग", "यह हरे फुदके (ग्रीन लीफहॉपर) से फैलने वाला विषाणु रोग है। संक्रमित पौधे ठीक नहीं होते; फुदके का नियंत्रण करें और संक्रमित पौधे जल्दी हटाएँ।",
   ["पत्तियाँ सिरे से पीली-नारंगी होने लगती हैं", "पौधे बौने, कल्ले कम", "नई पत्तियाँ मुड़ती हैं; बालियाँ छोटी, दाने आधे खाली"],
   "Thiamethoxam 25% WG (थायमेथोक्साम - हरे फुदके हेतु)", "0.2 ग्राम प्रति लीटर (40 ग्राम प्रति एकड़ 200 लीटर पानी में)", "नर्सरी में और रोपाई के 15 व 30 दिन बाद फुदके दिखने पर छिड़काव; इमिडाक्लोप्रिड 17.8% SL 0.25 मि.ली./लीटर से बदलें",
   ["फुदकों की निगरानी व नियंत्रण हेतु प्रकाश प्रपंच लगाएँ", "संक्रमित पौधे उखाड़कर दबा दें", "नर्सरी में नीम तेल (1500 ppm) 5 मि.ली./लीटर"],
   ["अपने राज्य हेतु अनुशंसित टुंग्रो-प्रतिरोधी किस्में लगाएँ", "पूरे गाँव में एक साथ रोपाई", "कटाई के बाद ठूँठ और अपने-आप उगे धान हटाएँ", "संक्रमित खेतों के पास रोपाई न करें"]],
  ["भातावरील टुंग्रो विषाणू", "हा हिरव्या तुडतुड्यांमुळे पसरणारा विषाणूजन्य रोग आहे. रोगट झाडे बरी होत नाहीत; तुडतुड्यांचे नियंत्रण करा व रोगट झाडे लवकर काढा.",
   ["पाने टोकापासून पिवळी-नारिंगी होतात", "झाडे खुजी, फुटवे कमी", "कोवळी पाने वळतात; लोंब्या लहान, दाणे अर्धवट पोचट"],
   "Thiamethoxam 25% WG (थायामेथोक्झाम - हिरव्या तुडतुड्यांसाठी)", "0.2 ग्रॅम प्रति लिटर (200 लिटर पाण्यात 40 ग्रॅम प्रति एकर)", "रोपवाटिकेत व लावणीनंतर 15 व 30 दिवसांनी तुडतुडे दिसताच फवारणी; इमिडाक्लोप्रिड 17.8% SL 0.25 मि.ली./लिटरने आलटून पालटून",
   ["तुडतुड्यांच्या पाहणी व नियंत्रणासाठी प्रकाश सापळे लावा", "रोगट चुडे उपटून गाडा", "रोपवाटिकेत निंबोळी तेल (1500 ppm) 5 मि.ली./लिटर"],
   ["आपल्या राज्यासाठी शिफारस केलेल्या टुंग्रो-प्रतिकारक जाती लावा", "संपूर्ण गावात एकाच वेळी लावणी", "काढणीनंतर धसकटे व आपोआप उगवलेला भात काढा", "रोगट शेतांजवळ लावणी टाळा"]],
  [tip(["Odisha", "West Bengal", "Andhra Pradesh", "Tamil Nadu", "Chhattisgarh"], ["kharif", "rabi"],
       "Eastern and southern rice belts see tungro outbreaks when leafhopper numbers rise; check nursery and young crop weekly.",
       "पूर्वी और दक्षिणी धान क्षेत्रों में फुदके बढ़ने पर टुंग्रो फैलता है; नर्सरी और छोटी फसल हर सप्ताह जाँचें।",
       "पूर्व व दक्षिण भात पट्ट्यात तुडतुडे वाढल्यास टुंग्रो पसरतो; रोपवाटिका व लहान पीक दर आठवड्याला तपासा.")])

E("rice_hispa", "rice", "pest", "Rice hispa beetle (Dicladispa armigera)",
  ["holes_chewing", "leaf_blight", "insects_underside"], "ICAR-NRRI Cuttack",
  ["Rice Hispa", "A small spiny blue-black beetle. Adults scrape the green tissue of leaves and grubs mine inside the leaf, so leaves turn white and dry.",
   ["White parallel streaks on leaves where green tissue is scraped", "Leaves look whitish and dry from the tip", "Small spiny dark beetles on leaves"],
   "Quinalphos 25% EC", "2 ml per litre (400 ml per acre in 200 L water)", "Spray when 1 adult or 1–2 damaged leaves per hill are seen; repeat after 15 days if needed",
   ["Clip and destroy leaf tips of seedlings before transplanting (removes eggs and grubs)", "Sweep with a hand net to collect beetles", "Neem seed kernel extract 5%"],
   ["Avoid excess nitrogen", "Remove grassy weeds from bunds", "Close planting spacing only as recommended"]],
  ["धान का हिस्पा कीट", "यह छोटा काँटेदार नीला-काला भृंग है। वयस्क पत्ती की हरी सतह खुरचते हैं और ग्रब पत्ती के अंदर सुरंग बनाते हैं, जिससे पत्तियाँ सफेद होकर सूखती हैं।",
   ["पत्तियों पर खुरची हुई सफेद समानांतर धारियाँ", "पत्तियाँ सिरे से सफेद होकर सूखती हैं", "पत्तियों पर छोटे काँटेदार काले भृंग"],
   "Quinalphos 25% EC (क्विनालफॉस)", "2 मि.ली. प्रति लीटर (400 मि.ली. प्रति एकड़ 200 लीटर पानी में)", "प्रति पौधा 1 वयस्क या 1–2 क्षतिग्रस्त पत्तियाँ दिखने पर छिड़काव; ज़रूरत हो तो 15 दिन बाद दोहराएँ",
   ["रोपाई से पहले पौध की पत्तियों के सिरे काटकर नष्ट करें (अंडे व ग्रब हटते हैं)", "हाथ के जाल से भृंग इकट्ठा करें", "5% नीम बीज अर्क"],
   ["अधिक नाइट्रोजन न दें", "मेड़ों से घास वाले खरपतवार हटाएँ", "अनुशंसित दूरी पर ही रोपाई"]],
  ["भातावरील हिस्पा (काटेरी भुंगेरा)", "हा लहान काटेरी निळसर-काळा भुंगेरा आहे. प्रौढ पानाचा हिरवा भाग खरवडतात व अळ्या पानात पोखरतात, त्यामुळे पाने पांढरी होऊन वाळतात.",
   ["पानांवर खरवडलेले पांढरे समांतर पट्टे", "पाने टोकाकडून पांढरी होऊन वाळतात", "पानांवर लहान काटेरी काळे भुंगेरे"],
   "Quinalphos 25% EC (क्विनॉलफॉस)", "2 मि.ली. प्रति लिटर (200 लिटर पाण्यात 400 मि.ली. प्रति एकर)", "प्रति चुडा 1 प्रौढ किंवा 1–2 खराब पाने दिसताच फवारणी; गरज असल्यास 15 दिवसांनी पुन्हा",
   ["लावणीपूर्वी रोपांच्या पानांचे शेंडे कापून नष्ट करा (अंडी व अळ्या जातात)", "हातजाळ्याने भुंगेरे गोळा करा", "5% निंबोळी अर्क"],
   ["जास्त नत्र टाळा", "बांधावरील गवतवर्गीय तण काढा", "शिफारशीप्रमाणेच अंतर ठेवा"]])

E("wheat_septoria", "wheat", "fungal", "Zymoseptoria tritici (Septoria tritici blotch)",
  ["brown_spots", "leaf_blight", "black_spots", "yellowing"], "ICAR-IIWBR Karnal",
  ["Wheat Septoria Leaf Blotch", "A fungal disease spread by rain splash from infected stubble; favoured by cool, wet weather.",
   ["Yellow patches that turn into long brown blotches on lower leaves", "Tiny black dots (fungal bodies) inside the blotches", "Disease moves up to the flag leaf in wet weather"],
   "Propiconazole 25% EC", "1 ml per litre (200 ml per acre)", "Spray when blotches reach the upper leaves; repeat after 15 days if wet weather continues. Alternative: Tebuconazole 25.9% EC 1 ml/L",
   ["Remove and burn infected stubble", "Avoid dense sowing"],
   ["Crop rotation with non-cereal crops", "Grow tolerant varieties", "Balanced nitrogen", "Timely sowing"]],
  ["गेहूँ का सेप्टोरिया पत्ती धब्बा", "यह फफूंद रोग संक्रमित ठूँठ से बारिश की छींटों द्वारा फैलता है; ठंडे, गीले मौसम में बढ़ता है।",
   ["निचली पत्तियों पर पीले धब्बे जो लंबे भूरे धब्बों में बदलते हैं", "धब्बों के अंदर छोटे काले बिंदु", "गीले मौसम में रोग ऊपर ध्वज पत्ती तक पहुँचता है"],
   "Propiconazole 25% EC (प्रोपिकोनाज़ोल)", "1 मि.ली. प्रति लीटर (200 मि.ली. प्रति एकड़)", "धब्बे ऊपरी पत्तियों तक पहुँचने पर छिड़काव; गीला मौसम रहे तो 15 दिन बाद दोहराएँ। विकल्प: टेबुकोनाज़ोल 25.9% EC 1 मि.ली./लीटर",
   ["संक्रमित ठूँठ हटाकर जलाएँ", "घनी बुवाई न करें"],
   ["गैर-अनाज फसलों के साथ फसल चक्र", "सहनशील किस्में लगाएँ", "संतुलित नाइट्रोजन", "समय पर बुवाई"]],
  ["गव्हावरील सेप्टोरिया पानांवरील डाग", "हा बुरशीजन्य रोग रोगट धसकटांवरून पावसाच्या शिंतोड्यांनी पसरतो; थंड, ओल्या हवामानात वाढतो.",
   ["खालच्या पानांवर पिवळे चट्टे जे लांब तपकिरी डागांत बदलतात", "डागांमध्ये लहान काळे ठिपके", "ओल्या हवामानात रोग वरच्या ध्वज पानापर्यंत पोहोचतो"],
   "Propiconazole 25% EC (प्रोपिकोनाझोल)", "1 मि.ली. प्रति लिटर (200 मि.ली. प्रति एकर)", "डाग वरच्या पानांपर्यंत पोहोचताच फवारणी; ओले हवामान राहिल्यास 15 दिवसांनी पुन्हा. पर्याय: टेब्युकोनाझोल 25.9% EC 1 मि.ली./लिटर",
   ["रोगट धसकटे काढून जाळा", "दाट पेरणी टाळा"],
   ["तृणधान्येतर पिकांसोबत फेरपालट", "सहनशील जाती लावा", "संतुलित नत्र", "वेळेवर पेरणी"]])

E("cotton_alternaria", "cotton", "fungal", "Alternaria macrospora",
  ["brown_spots", "concentric_rings", "yellowing"], "ICAR-CICR Nagpur",
  ["Cotton Alternaria Leaf Spot", "A fungal leaf spot that increases in humid weather and on potash-deficient or stressed plants.",
   ["Small brown round spots with rings on older leaves", "Spots join, leaves turn yellow and drop early", "Spots may also appear on bracts and bolls"],
   "Mancozeb 75% WP", "2.5 g per litre (500 g per acre)", "Spray at first spots; repeat after 15 days. Alternative: Propiconazole 25% EC 1 ml/L",
   ["Remove and destroy fallen infected leaves", "Spray Pseudomonas fluorescens 10 g/L"],
   ["Apply potash as per soil test", "Avoid water stress", "Destroy crop residue after harvest"]],
  ["कपास का अल्टरनेरिया पत्ती धब्बा", "यह फफूंद पत्ती धब्बा रोग नम मौसम में और पोटाश की कमी वाले या कमज़ोर पौधों पर बढ़ता है।",
   ["पुरानी पत्तियों पर छल्लों वाले छोटे भूरे गोल धब्बे", "धब्बे मिलकर पत्तियाँ पीली होकर जल्दी गिरती हैं", "सहपत्रों और टिंडों पर भी धब्बे"],
   "Mancozeb 75% WP (मैंकोज़ेब)", "2.5 ग्राम प्रति लीटर (500 ग्राम प्रति एकड़)", "पहले धब्बे पर छिड़काव; 15 दिन बाद दोहराएँ। विकल्प: प्रोपिकोनाज़ोल 25% EC 1 मि.ली./लीटर",
   ["गिरी संक्रमित पत्तियाँ हटाकर नष्ट करें", "स्यूडोमोनास 10 ग्राम/लीटर छिड़कें"],
   ["मिट्टी जाँच अनुसार पोटाश दें", "पानी की कमी न होने दें", "कटाई के बाद फसल अवशेष नष्ट करें"]],
  ["कापसावरील अल्टरनेरिया पानठिपके", "हा बुरशीजन्य पानठिपका दमट हवामानात आणि पोटॅशची कमतरता असलेल्या किंवा कमकुवत झाडांवर वाढतो.",
   ["जुन्या पानांवर कड्यांचे लहान तपकिरी गोल ठिपके", "ठिपके एकत्र येऊन पाने पिवळी पडून लवकर गळतात", "पुष्पकोश व बोंडांवरही ठिपके"],
   "Mancozeb 75% WP (मॅन्कोझेब)", "2.5 ग्रॅम प्रति लिटर (500 ग्रॅम प्रति एकर)", "पहिले ठिपके दिसताच फवारणी; 15 दिवसांनी पुन्हा. पर्याय: प्रोपिकोनाझोल 25% EC 1 मि.ली./लिटर",
   ["गळालेली रोगट पाने गोळा करून नष्ट करा", "स्युडोमोनास 10 ग्रॅम/लिटर फवारा"],
   ["माती परीक्षणानुसार पोटॅश द्या", "पाण्याचा ताण टाळा", "काढणीनंतर पीक अवशेष नष्ट करा"]])

E("cotton_wilt", "cotton", "fungal", "Fusarium oxysporum f. sp. vasinfectum / Verticillium dahliae (soil-borne)",
  ["wilting", "yellowing", "stunted"], "ICAR-CICR Nagpur",
  ["Cotton Wilt (Fusarium / Verticillium)", "Soil-borne fungi block the water-carrying tissue of the plant. Once a plant wilts it cannot be cured; protect the rest of the field and the next crop.",
   ["Leaves turn yellow between veins and droop; lower leaves first", "Whole plant wilts and dries; stunted growth", "Brown or black streaks inside the stem when cut"],
   "Carbendazim 50% WP (soil drench around affected and nearby plants)", "1 g per litre, pour 100–200 ml at the root zone of each plant", "Drench at first wilting in patches; seed treatment with Carbendazim 2 g/kg seed before sowing",
   ["Seed treatment with Trichoderma viride 4 g/kg seed", "Apply 2 kg Trichoderma mixed in 100 kg FYM per acre before sowing", "Uproot and burn wilted plants"],
   ["Grow wilt-tolerant varieties (desi cotton is resistant to Fusarium wilt)", "Crop rotation with cereals for 2–3 years", "Avoid waterlogging", "Balanced NPK with potash"]],
  ["कपास का उकठा रोग (फ्यूज़ेरियम / वर्टिसिलियम)", "मिट्टी में रहने वाली फफूंद पौधे की पानी ले जाने वाली नलिकाएँ बंद कर देती है। मुरझाया पौधा ठीक नहीं होता; बाकी खेत और अगली फसल को बचाएँ।",
   ["नसों के बीच पत्तियाँ पीली होकर लटकती हैं; पहले निचली पत्तियाँ", "पूरा पौधा मुरझाकर सूख जाता है; बढ़वार रुकती है", "तना काटने पर अंदर भूरी या काली धारियाँ"],
   "Carbendazim 50% WP (कार्बेन्डाज़िम - प्रभावित व आसपास के पौधों की जड़ में)", "1 ग्राम प्रति लीटर, हर पौधे की जड़ में 100–200 मि.ली. डालें", "पहली बार उकठा दिखने पर जड़ में डालें; बुवाई से पहले कार्बेन्डाज़िम 2 ग्राम/किलो बीज से बीज उपचार",
   ["ट्राइकोडर्मा विरिडी 4 ग्राम/किलो बीज से बीज उपचार", "बुवाई से पहले 2 किलो ट्राइकोडर्मा 100 किलो गोबर खाद में मिलाकर प्रति एकड़ डालें", "मुरझाए पौधे उखाड़कर जलाएँ"],
   ["उकठा-सहनशील किस्में लगाएँ (देसी कपास फ्यूज़ेरियम उकठा प्रतिरोधी)", "2–3 साल अनाज फसलों के साथ फसल चक्र", "जलभराव न होने दें", "पोटाश सहित संतुलित NPK"]],
  ["कापसावरील मर रोग (फ्युजेरियम / व्हर्टिसिलियम)", "जमिनीतील बुरशी झाडाच्या पाणी वाहणाऱ्या नलिका बंद करते. मलूल झाड बरे होत नाही; उरलेले शेत व पुढील पीक वाचवा.",
   ["शिरांमधील पाने पिवळी पडून लोंबतात; आधी खालची पाने", "संपूर्ण झाड मलूल होऊन वाळते; वाढ खुंटते", "खोड कापल्यास आत तपकिरी किंवा काळ्या रेषा"],
   "Carbendazim 50% WP (कार्बेन्डाझिम - बाधित व आजूबाजूच्या झाडांच्या मुळांशी)", "1 ग्रॅम प्रति लिटर, प्रत्येक झाडाच्या मुळाशी 100–200 मि.ली. ओता", "पहिल्यांदा मर दिसताच मुळाशी ओता; पेरणीपूर्वी कार्बेन्डाझिम 2 ग्रॅम/किलो बीजप्रक्रिया",
   ["ट्रायकोडर्मा 4 ग्रॅम/किलो बीजप्रक्रिया", "पेरणीपूर्वी 2 किलो ट्रायकोडर्मा 100 किलो शेणखतात मिसळून एकरी द्या", "मलूल झाडे उपटून जाळा"],
   ["मर-सहनशील जाती लावा (देशी कापूस फ्युजेरियम मरला प्रतिकारक)", "2–3 वर्षे तृणधान्यांसोबत फेरपालट", "पाणी साचू देऊ नका", "पोटॅशसह संतुलित NPK"]])

# ---------------- HEALTHY ----------------
E("healthy", "any", "healthy", "", [], ICAR,
  ["Healthy Plant", "No disease detected. Your plant looks healthy!", ["Green, uniform leaves without spots"],
   "No spray needed", "—", "Do not spray pesticides on a healthy crop",
   ["Continue using compost / FYM and neem cake", "Install yellow sticky traps for early pest warning"],
   ["Inspect the crop every week", "Balanced fertiliser based on soil test", "Keep the field weed-free and well-drained"]],
  ["स्वस्थ पौधा", "कोई रोग नहीं मिला। आपका पौधा स्वस्थ दिखता है!", ["बिना धब्बों वाली हरी, एकसमान पत्तियाँ"],
   "छिड़काव की ज़रूरत नहीं", "—", "स्वस्थ फसल पर कीटनाशक न छिड़कें",
   ["कम्पोस्ट / गोबर खाद और नीम खली का उपयोग जारी रखें", "कीटों की जल्दी पहचान हेतु पीले चिपचिपे ट्रैप लगाएँ"],
   ["हर सप्ताह फसल की जाँच करें", "मिट्टी जाँच के आधार पर संतुलित खाद", "खेत खरपतवार मुक्त और अच्छी जल निकासी वाला रखें"]],
  ["निरोगी झाड", "कोणताही रोग आढळला नाही. तुमचे झाड निरोगी दिसते!", ["ठिपके नसलेली हिरवी, एकसारखी पाने"],
   "फवारणीची गरज नाही", "—", "निरोगी पिकावर कीटकनाशक फवारू नका",
   ["कंपोस्ट / शेणखत व निंबोळी पेंड वापरणे सुरू ठेवा", "किडीच्या लवकर ओळखीसाठी पिवळे चिकट सापळे लावा"],
   ["दर आठवड्याला पिकाची पाहणी करा", "माती परीक्षणावर आधारित संतुलित खत", "शेत तणमुक्त व चांगल्या निचऱ्याचे ठेवा"]])


AUTO = Path(__file__).resolve().parent.parent / "data" / "kb_auto_translations.json"
AUTO_TR = json.loads(AUTO.read_text(encoding="utf-8")) if AUTO.exists() else {}  # from translate_kb.py (te/ta/bn)
NOT_SPRAYS = {"cotton_wilt", "grape_esca"}  # root drench / wound paste: the per-tank spray calculator does not apply


def dose_per_litre(d, dosage_en):
    m = re.match(r"\s*([\d.]+)\s*(g|ml) per litre", dosage_en)
    return {"amount": float(m.group(1)), "unit": m.group(2)} if m and d["id"] not in NOT_SPRAYS else None


def expand(d):
    content = {}
    for lang, v in d.pop("L").items():
        name, about, symptoms, product, dosage, timing, organic, prevention = v
        content[lang] = {
            "name": name, "about": about, "symptoms": symptoms,
            "chemical": {"product": product, "dosage": dosage, "timing": timing, "safety": SAFETY[lang]},
            "organic": organic, "prevention": prevention, "warning": WARNING[lang],
        }
    en = content["en"]
    for lang, tr in AUTO_TR.items():  # machine translations; product names stay in English like on the label
        f = lambda x: tr.get(x, x)  # noqa: E731
        content[lang] = {
            # machine-translated disease names can be too literal, so keep the English name alongside
            "name": f"{f(en['name'])} ({en['name']})" if f(en["name"]) != en["name"] else en["name"], "about": f(en["about"]), "symptoms": [f(x) for x in en["symptoms"]],
            "chemical": {"product": en["chemical"]["product"], "dosage": f(en["chemical"]["dosage"]),
                         "timing": f(en["chemical"]["timing"]), "safety": [f(x) for x in en["chemical"]["safety"]]},
            "organic": [f(x) for x in en["organic"]], "prevention": [f(x) for x in en["prevention"]],
            "warning": f(en["warning"]), "auto_translated": True,
        }
        for t in d["region_tips"]:
            t["tip"][lang] = f(t["tip"]["en"])
    d["content"] = content
    d["dose_per_litre"] = dose_per_litre(d, en["chemical"]["dosage"])
    return d


out = Path(__file__).resolve().parent.parent / "data" / "diseases.json"
out.write_text(json.dumps({"diseases": [expand(d) for d in D]}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Wrote {len(D)} entries to {out}")
