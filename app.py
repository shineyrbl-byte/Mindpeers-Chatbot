from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model= genai.GenerativeModel("gemini-2.0-flash")
conversation_history =[]
mood_history= []

SYSTEM_PROMPT = """
You are MindPeers AI, an emotionally intelligent mental wellness assistant.

Your purpose is to help users explore emotions, mental wellbeing, stressors, and coping strategies in a supportive and non-judgmental way.
Respond like a supportive mental wellness coach.

You can discuss:
- mental health
- emotions
- stress
- anxiety
- burnout
- loneliness
- low mood
- self-esteem
- relationships
- family concerns
- work stress
- academic pressure
- career uncertainty
- sleep issues
- wellbeing
- emotional resilience
- coping strategies

If a user asks something completely unrelated to mental wellbeing
(e.g. coding, mathematics, sports scores, politics, geography),
politely explain that you are focused on emotional wellbeing and mental health support.

Avoid:

- Mentioning emergency services unless risk level is High.

- Repeating the same advice already shown in coping tips.

- Sounding robotic or generic.   add these too.. or are these added already

When the user describes emotions, before responding:
1. Identify the user's likely emotional state.
2. Acknowledge the user's feelings.
3. Consider possible triggers or stressors.
4. Briefly explain what may be happening with the user.
5. Respond gently with empathy.
6. Offer practical emotional support.
7. Offer one or two practical coping techniques.
8. End with a gentle and thoughtful follow-up question when appropriate.

Possible emotions:
- Stress
- Anxiety
- Burnout
- Loneliness
- Low Mood
- General

Response Guidelines:

- Sound warm, calm and human.
- Avoid robotic language.
- Avoid repeating the same advice.
- Avoid giving medical diagnoses.
- Do not immediately suggest professional help unless the situation warrants it.
- Keep responses conversational.
- Validate emotions without making assumptions.

For users experiencing:
Stress:
- help them prioritize and slow down
- suggest small actionable steps

Anxiety:
- encourage grounding techniques
- help separate worries from facts

Burnout:
- encourage rest, boundaries and recovery

Loneliness:
- encourage meaningful connection and self-compassion

Low Mood:
- encourage small achievable activities and emotional expression

If the user expresses hopelessness, self-harm thoughts, suicidal thoughts, or says things like:
- "I want to die"
- "I don't want to exist"
- "I want to disappear"
- "Everyone would be better without me"

respond with empathy, encourage contacting trusted people, and advise seeking immediate professional or emergency support if they are in danger.

Never shame, judge, or dismiss a user's feelings.
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():

    user_message = request.json.get('message')

    message = user_message.lower()

# Emotion Detection
    detected_emotions = []

    if any(word in message for word in ["stress", "stressed", "pressure", "overwhelmed"]):
        detected_emotions.append("Stress")

    if any(word in message for word in ["anxious", "anxiety", "worried", "panic", "nervous", "fear", "scared"]):
        detected_emotions.append("Anxiety")
    
    if any(word in message for word in ["burnout", "burned out", "burnt out", "exhausted", "drained"]):
        detected_emotions.append("Burnout")

    if any(word in message for word in ["lonely", "alone", "isolated"]):
        detected_emotions.append("Loneliness")

    if any(word in message for word in ["sad", "depressed", "hopeless", "empty", "worthless"]):
        detected_emotions.append("Low Mood")
    if not detected_emotions:
        detected_emotions.append("General")

    primary_emotion = detected_emotions[0]
    mood_history.append(primary_emotion)
    if len(mood_history) > 5:
        mood_history.pop(0)


    trigger_mapping = {
    "exam": "Academic Pressure",
    "study": "Academic Pressure",
    "career": "Career Uncertainty",
    "job": "Career Uncertainty",
    "work": "Workplace Stress",
    "boss": "Workplace Stress",
    "family": "Family Conflict",
    "relationship": "Relationship Issues",
    "money": "Financial Stress",
    "finance": "Financial Stress",
    "lonely": "Social Isolation"
}
    
    def detect_trigger(text):
        text = text.lower()
        for keyword, trigger in trigger_mapping.items():
            if keyword in text:
                return trigger
        return "General Life Stress"
    
    def detect_burnout(text):
        text = text.lower()
        severe_words = [
        "burnout",
        "burned out",
        "burnt out",
        "completely exhausted"
    ]
        moderate_words = [
        "drained",
        "overworked",
        "tired"
    ]
        if any(word in text for word in severe_words):
            return "High"
        if any(word in text for word in moderate_words):
            return "Moderate"
        return "Low"
    
    def detect_sleep_issue(text):
        sleep_words = [
        "can't sleep",
        "insomnia",
        "sleeping badly",
        "sleep problem",
        "not sleeping"
    ]
        return any(word in text.lower() for word in sleep_words)
    
    def detect_strength(text):
        text = text.lower()
        if "trying my best" in text:
            return "Resilience"
        elif "working hard" in text:
            return "Determination"
        elif "hope" in text:
            return "Optimism"
        return None

    # Risk Classification

    risk_level = "Low"

    if any(word in message for word in [
        "hopeless",
        "worthless",
        "giving up",
        "nobody cares",
        "no one cares"
        ]):
        risk_level = "Medium"

    recommended_action = "Self-Help Resources"
    if risk_level == "Medium":
        recommended_action = "Book Therapist Session"

    def calculate_wellness_score(
            risk_level,
            emotion,
            burnout_index,
            sleep_issue
        ):
        score = 100
        if emotion == "Stress":
            score -= 10

        elif emotion == "Anxiety":
            score -= 15

        elif emotion == "Burnout":
            score -= 20

        elif emotion == "Low Mood":
            score -= 25

        elif emotion == "Loneliness":
            score -= 15

    # Burnout

        if burnout_index == "Moderate":
            score -= 10

    # Sleep

        if sleep_issue:
            score -= 10

    # Risk

        if risk_level == "Medium":
            score -= 20

        elif risk_level == "High":
            score -= 40

        return max(score, 0)
        
    trigger = detect_trigger(user_message)
    burnout_index = detect_burnout(user_message)
    sleep_issue = detect_sleep_issue(user_message)
    strength = detect_strength(user_message)
    wellness_score = calculate_wellness_score(
        risk_level,
        primary_emotion,
        burnout_index,
        sleep_issue
    )
    
    # Therapist Recommendation
    professional_mapping = {

    "Academic Pressure": "Counselling Psychologist",

    "Career Uncertainty": "Career Counsellor",

    "Workplace Stress": "Workplace Wellness Specialist",

    "Family Conflict": "Family Therapist",

    "Relationship Issues": "Couple Therapist",

    "Financial Stress": "Counselling Psychologist",

    "Social Isolation": "Psychotherapist",

    "Stress": "Counselling Psychologist",

    "Anxiety": "Counselling Psychologist",

    "Burnout": "Workplace Wellness Specialist",

    "Low Mood": "Clinical Psychologist",

    "Loneliness": "Psychotherapist",

    "Relationship": "Couple Therapist",

    "Family": "Family Therapist",

    "Trauma": "Trauma Therapist",

    "Addiction": "Addiction Counsellor",

    "Career": "Career Counsellor"
}
    
    therapist_type = professional_mapping.get(
        trigger,
        professional_mapping.get(
            primary_emotion,
            "General Wellness Coach"
        )
    )
    
    if sleep_issue:
        therapist_type = "Sleep Specialist"


    resource = "General Wellness Articles"

    if primary_emotion == "Anxiety":
        resource = "5-Minute Breathing Exercise"

    elif primary_emotion == "Stress":
        resource = "Stress Management Guide"

    elif primary_emotion == "Burnout":
        resource = "Burnout Recovery Tips"

    elif primary_emotion == "Loneliness":
        resource = "Social Connection Activities"

    elif primary_emotion == "Low Mood":
        resource = "Positive Habit Building Guide"


    # Coping Tips

    coping_tips = []

    if primary_emotion == "Anxiety":
        coping_tips = [
            "Practice deep breathing exercises",
            "Break large tasks into smaller steps",
            "Focus on what you can control"
        ]

    elif primary_emotion == "Stress":
        coping_tips = [
        "Take short breaks throughout the day",
        "Create a simple task priority list",
        "Maintain a healthy sleep routine"
    ]

    elif primary_emotion == "Loneliness":
        coping_tips = [
        "Reach out to a trusted friend",
        "Participate in a social activity",
        "Spend time with supportive people"
    ]

    elif primary_emotion == "Low Mood":
        coping_tips = [
        "Engage in a small enjoyable activity",
        "Talk to someone you trust",
        "Maintain regular daily routines"
    ]

    elif primary_emotion == "Burnout":
        coping_tips = [
        "Take meaningful rest periods",
        "Reduce unnecessary commitments",
        "Set realistic expectations for yourself"
    ]
        
    if not coping_tips:
        coping_tips = [
        "Take a short break and reflect on your thoughts",
        "Talk to someone you trust",
        "Focus on one small step at a time"
    ]
        
    personalized_plan = []
    if primary_emotion == "Stress":
        personalized_plan = [
        "Take a 10 minute break today",
        "Complete your top 3 tasks",
        "Sleep before midnight"
    ]
    elif primary_emotion == "Anxiety":
        personalized_plan = [
        "Practice breathing for 5 minutes",
        "Write down your worries",
        "Focus on one task at a time"
    ]
    elif primary_emotion == "Burnout":
        personalized_plan = [
        "Reduce workload where possible",
        "Take a meaningful break",
        "Set healthier boundaries"
    ]

    elif primary_emotion == "Low Mood":
        personalized_plan = [
        "Go for a short walk",
        "Connect with a trusted person",
        "Engage in an enjoyable activity"
    ]

    elif primary_emotion == "Loneliness":
        personalized_plan = [
        "Reach out to one friend",
        "Join a social activity",
        "Spend time outside"
    ]
     
     # CRISIS DETECTION  
    crisis_phrases = [
    # Direct suicide/self-harm
    "suicide",
    "suicidal",
    "kill myself",
    "want to kill myself",
    "end my life",
    "take my life",
    "i want to die",
    "want to die",
    "wish i was dead",
    "better off dead",

    # Hopelessness / existence
    "don't want to live",
    "dont want to live",
    "i don't want to live",
    "i dont want to live",
    "don't want to exist",
    "dont want to exist",
    "i don't want to exist",
    "i dont want to exist",
    "want to disappear",
    "wish i could disappear",
    "wish i could vanish",

    # Self-harm
    "self harm",
    "self-harm",
    "hurt myself",
    "harm myself",
    "cut myself",
    "injure myself",
    "burn myself",

    # Giving up
    "can't do this anymore",
    "cant do this anymore",
    "cannot do this anymore",
    "can't go on",
    "cant go on",
    "cannot go on",
    "i give up",
    "giving up on life",

    # Severe hopelessness
    "there is no point",
    "no reason to live",
    "life is meaningless",
    "nobody would miss me",
    "everyone would be better without me",
    "i am a burden",
    "i feel like a burden",

    # Planning language
    "i have a plan",
    "i made a plan",
    "i know how i would do it",
    "thinking about ending my life",
    "thinking about suicide"
]

    if any(phrase in user_message.lower() for phrase in crisis_phrases):
        return jsonify({
            "emotion": primary_emotion,
            "risk_level": "High",
            "trigger": trigger,
            "burnout_index": burnout_index,
            "strength": strength,
            "recommended_action": "Immediate Professional Support",
            "therapist_type": "Clinical Psychologist",
            "resource": "Emergency Mental Health Support",
            "recent_moods": " → ".join(mood_history),
            "coping_tips": [
                "Reach out to a trusted person immediately",
                "Contact professional support",
                "Do not stay isolated"
                ],
            "personalized_plan": [
                "Contact a trusted person now",
                "Seek immediate professional support",
                "Avoid staying alone if possible"
                ],
            "session_summary": """
High Risk Emotional State Detected

Recommended:
Immediate Professional Support

Suggested Professional:
Clinical Psychologist
""",

    "reply": """I'm really sorry you're feeling this way.

If you're thinking about harming yourself or feel unable to stay safe, please contact emergency services or a crisis helpline immediately.

You don't have to handle this alone. Consider reaching out to a trusted friend, family member, counselor, or mental health professional right now.

Can you tell me if you're currently in immediate danger or thinking about acting on these thoughts?"""
})

    try:

        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        messages= [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ] + conversation_history

        prompt= SYSTEM_PROMPT + "\n\nUser message: " + user_message
        response= model.generate_content(prompt)

        print("TYPE:", type(response))
        print("RESPONSE:", response)

        bot_reply = response.text

        conversation_history.append({
            "role": "assistant",
            "content": bot_reply
        })

        if len(conversation_history) > 50:
            conversation_history[:]= conversation_history[-50:]

        print("BOT REPLY:", bot_reply)

        recent_moods = " → ".join(mood_history)

        session_summary = f"""
        Primary Emotion: {primary_emotion}
        Trigger: {trigger}
        Risk Level: {risk_level}
        Burnout Index: {burnout_index}
        Strength: {strength}
        Recommended Professional: {therapist_type}
        Recommended Action: {recommended_action}
"""

        response_data = {
            "emotion": primary_emotion,
            "all_emotions": detected_emotions,
            "risk_level": risk_level,
            "trigger": trigger,
            "burnout_index": burnout_index,
            "strength": strength,
            "wellness_score": wellness_score,
            "sleep_issue": sleep_issue,
            "recommended_action": recommended_action,
            "therapist_type": therapist_type,
            "coping_tips": coping_tips,
            "personalized_plan": personalized_plan,
            "resource": resource,
            "recent_moods": recent_moods,
            "session_summary": session_summary,
            "reply": bot_reply}
        print("JSON SENT:", response_data)
        return jsonify(response_data)
    except Exception as e:
        print("========== GEMINI ERROR ==========")
        print(str(e))
        print("==================================")
        return jsonify({
            "reply": f"Error: {str(e)}"
            })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))