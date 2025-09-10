"""
LocalMind Healthcare Domain

Specialized healthcare capabilities providing medical information, first aid guidance,
and health education while maintaining appropriate disclaimers and safety measures.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HealthcareResponse:
    """Structure for healthcare responses."""
    content: str
    category: str
    urgency_level: str
    disclaimer: str
    emergency_guidance: Optional[str]
    follow_up_recommendations: List[str]
    sources: List[str]

class HealthcareDomain:
    """
    Healthcare domain for LocalMind's medical information assistance.
    
    Features:
    - Medical information and education
    - First aid guidance
    - Symptom information (with disclaimers)
    - Preventive care guidance
    - Emergency response information
    - Health and wellness tips
    
    IMPORTANT: All medical information includes appropriate disclaimers
    and emphasizes the need for professional medical consultation.
    """
    
    def __init__(self, config: Dict[str, Any], model_engine=None, vector_db=None, conversation_memory=None):
        self.config = config
        self.model_engine = model_engine
        self.vector_db = vector_db
        self.conversation_memory = conversation_memory
        self.logger = logging.getLogger(__name__)
        
        # Healthcare configuration
        self.categories = config['domains']['healthcare']['categories']
        self.disclaimer_required = config['domains']['healthcare']['disclaimer_required']
        self.emergency_redirect = config['domains']['healthcare']['emergency_redirect']
        
        # Medical disclaimers and emergency information
        self.medical_disclaimer = self._get_medical_disclaimer()
        self.emergency_guidance = self._get_emergency_guidance()
        
        # Healthcare knowledge categories
        self.urgency_keywords = self._initialize_urgency_detection()
        self.emergency_keywords = self._initialize_emergency_detection()
        
        self.logger.info("HealthcareDomain initialized")
        self.logger.info(f"Categories: {', '.join(self.categories)}")
        self.logger.info("Medical disclaimers enabled")
    
    def _get_medical_disclaimer(self) -> str:
        """Get standard medical disclaimer."""
        return """
⚠️ IMPORTANT MEDICAL DISCLAIMER ⚠️

This information is provided for educational purposes only and is not intended to:
• Replace professional medical advice, diagnosis, or treatment
• Substitute for consultation with qualified healthcare providers
• Provide specific medical recommendations for individual cases

ALWAYS seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay seeking it because of information provided here.

If you think you may have a medical emergency, call your local emergency services immediately.
"""
    
    def _get_emergency_guidance(self) -> str:
        """Get emergency response guidance."""
        return """
🚨 EMERGENCY SITUATIONS 🚨

If you are experiencing a medical emergency, please:

1. Call your local emergency number immediately:
   • US/Canada: 911
   • Europe: 112
   • UK: 999
   • Australia: 000

2. For poison emergencies:
   • US: 1-800-222-1222 (Poison Control)

3. If you cannot call:
   • Ask someone nearby to call for you
   • Go to the nearest emergency room
   • Flag down emergency services

Signs of medical emergencies include:
• Chest pain or difficulty breathing
• Severe bleeding or injury
• Loss of consciousness
• Severe allergic reactions
• Signs of stroke (face drooping, arm weakness, speech difficulty)
• Severe burns or electrical shock
"""
    
    def _initialize_urgency_detection(self) -> Dict[str, List[str]]:
        """Initialize keywords for urgency level detection."""
        return {
            'emergency': [
                'chest pain', 'can\'t breathe', 'unconscious', 'severe bleeding',
                'poisoning', 'overdose', 'stroke symptoms', 'heart attack',
                'severe allergic reaction', 'choking', 'severe burn'
            ],
            'urgent': [
                'severe pain', 'high fever', 'difficulty breathing', 'vomiting blood',
                'severe headache', 'sudden vision loss', 'severe dizziness',
                'broken bone', 'deep cut', 'severe abdominal pain'
            ],
            'moderate': [
                'pain', 'fever', 'headache', 'nausea', 'rash', 'cough',
                'sore throat', 'fatigue', 'minor injury', 'upset stomach'
            ],
            'low': [
                'prevention', 'general health', 'wellness', 'nutrition',
                'exercise', 'sleep', 'vitamins', 'routine care'
            ]
        }
    
    def _initialize_emergency_detection(self) -> List[str]:
        """Initialize keywords that trigger emergency responses."""
        return [
            'emergency', 'urgent', 'serious', 'severe', 'critical',
            'bleeding', 'unconscious', 'overdose', 'poisoning',
            'heart attack', 'stroke', 'can\'t breathe', 'choking'
        ]
    
    def process_healthcare_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> HealthcareResponse:
        """
        Process a healthcare query with appropriate safety measures.
        
        Args:
            query: User's health-related question
            user_context: Optional user context (age, location, etc.)
            
        Returns:
            Healthcare response with safety measures and disclaimers
        """
        try:
            # Get conversation context for memory integration
            conversation_context = ""
            if self.conversation_memory:
                try:
                    relevant_context = self.conversation_memory.get_relevant_context(query, limit=3)
                    if relevant_context:
                        conversation_context = "\n".join([
                            f"Previous: {ctx['query']} → {ctx['response'][:100]}..."
                            for ctx in relevant_context
                        ])
                except Exception as e:
                    self.logger.warning(f"Failed to get conversation context: {e}")
            
            # Detect urgency level
            urgency_level = self._detect_urgency_level(query)
            
            # Check for emergency situations
            if urgency_level == 'emergency':
                return self._create_emergency_response(query)
            
            # Detect healthcare category
            category = self._detect_healthcare_category(query)
            
            # Get relevant medical context
            medical_context = self._get_medical_context(query, category)
            
            # Build healthcare-specific prompt with conversation context
            enhanced_prompt = self._build_healthcare_prompt(
                query, category, urgency_level, medical_context, conversation_context
            )
            
            # Generate response using model
            if self.model_engine and self.model_engine.is_loaded:
                response_content = self.model_engine.generate_response(enhanced_prompt)
            else:
                response_content = self._generate_fallback_response(query, category)
            
            # Store in conversation memory
            if self.conversation_memory:
                try:
                    self.conversation_memory.add_conversation(query, response_content, domain="healthcare")
                except Exception as e:
                    self.logger.warning(f"Failed to store conversation: {e}")
            
            # Create structured healthcare response
            healthcare_response = self._create_healthcare_response(
                response_content, query, category, urgency_level
            )
            
            self.logger.debug(f"Healthcare query processed: {category} - {urgency_level}")
            return healthcare_response
            
        except Exception as e:
            self.logger.error(f"Healthcare query processing failed: {e}")
            return self._create_error_response(query)
    
    def _detect_urgency_level(self, query: str) -> str:
        """Detect the urgency level of a healthcare query."""
        query_lower = query.lower()
        
        # Check for emergency keywords first
        for keyword in self.urgency_keywords['emergency']:
            if keyword in query_lower:
                return 'emergency'
        
        # Check other urgency levels
        for level in ['urgent', 'moderate', 'low']:
            for keyword in self.urgency_keywords[level]:
                if keyword in query_lower:
                    return level
        
        # Default to moderate for unknown queries
        return 'moderate'
    
    def _detect_healthcare_category(self, query: str) -> str:
        """Detect the healthcare category from the query."""
        query_lower = query.lower()
        
        category_keywords = {
            'first_aid': [
                'first aid', 'emergency', 'bleeding', 'burn', 'cut', 'injury',
                'sprain', 'wound', 'bandage', 'treatment'
            ],
            'preventive_care': [
                'prevention', 'healthy', 'diet', 'exercise', 'wellness',
                'nutrition', 'vitamins', 'lifestyle', 'habits'
            ],
            'symptoms': [
                'symptoms', 'pain', 'fever', 'headache', 'nausea', 'rash',
                'cough', 'sore throat', 'fatigue', 'dizziness'
            ],
            'medication_info': [
                'medication', 'medicine', 'drug', 'prescription', 'dosage',
                'side effects', 'interaction', 'pills', 'treatment'
            ]
        }
        
        # Score each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            category_scores[category] = score
        
        # Return category with highest score
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general_health'
    
    def _get_medical_context(self, query: str, category: str) -> str:
        """Retrieve relevant medical context from knowledge base."""
        if not self.vector_db:
            return ""
        
        try:
            # Search for relevant healthcare content
            results = self.vector_db.search_by_domain(query, 'healthcare', k=3)
            
            # Filter by category if possible
            category_results = [r for r in results if r['metadata'].get('category') == category]
            if category_results:
                results = category_results
            
            # Combine relevant content
            context_parts = []
            for result in results[:2]:  # Use top 2 results
                context_parts.append(result['document'])
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to get medical context: {e}")
            return ""
    
    def _build_healthcare_prompt(self, query: str, category: str, urgency: str, context: str, conversation_context: str = "") -> str:
        """Build healthcare-specific prompt with safety measures."""
        base_prompt = """You are a knowledgeable health information assistant. Provide accurate, 
evidence-based health information while emphasizing the importance of professional medical care.

IMPORTANT GUIDELINES:
- Always include appropriate medical disclaimers
- Never provide specific medical diagnoses
- Emphasize when to seek professional medical help
- Focus on general health education and first aid information
- Be especially careful with medication information
- Encourage preventive care and healthy lifestyle choices"""
        
        urgency_instructions = {
            'emergency': 'CRITICAL: Emphasize immediate emergency care and calling emergency services.',
            'urgent': 'URGENT: Strongly recommend seeking medical attention soon.',
            'moderate': 'Provide helpful information but emphasize consulting healthcare providers.',
            'low': 'Focus on general health education and wellness information.'
        }
        
        category_instructions = {
            'first_aid': 'Provide clear, step-by-step first aid instructions. Emphasize safety and when to call for help.',
            'preventive_care': 'Focus on evidence-based prevention strategies and healthy lifestyle choices.',
            'symptoms': 'Provide general information about symptoms but never diagnose. Emphasize professional evaluation.',
            'medication_info': 'Provide general medication information but emphasize consulting pharmacists and doctors.'
        }
        
        prompt_parts = [
            base_prompt,
            f"\nUrgency Level: {urgency}",
            f"Urgency Instructions: {urgency_instructions.get(urgency, '')}",
            f"\nCategory: {category}",
            f"Category Instructions: {category_instructions.get(category, '')}",
        ]
        
        # Add conversation context if available
        if conversation_context:
            prompt_parts.append(f"\nPrevious Conversation Context:\n{conversation_context}")
        
        # Add context if available
        if context:
            prompt_parts.append(f"\nRelevant Medical Information:\n{context}")
        
        # Add the query
        prompt_parts.extend([
            f"\nUser Question: {query}",
            "\nProvide a comprehensive response that includes:",
            "1. Accurate health information based on current medical knowledge",
            "2. Clear safety instructions if applicable",
            "3. When to seek professional medical help",
            "4. Appropriate medical disclaimers",
            "5. Follow-up recommendations",
            "\nResponse:"
        ])
        
        return '\n'.join(prompt_parts)
    
    def _create_emergency_response(self, query: str) -> HealthcareResponse:
        """Create immediate emergency response."""
        emergency_content = f"""
🚨 MEDICAL EMERGENCY DETECTED 🚨

Based on your query, this may be a medical emergency that requires IMMEDIATE attention.

{self.emergency_guidance}

While waiting for emergency services:
• Stay calm and keep the person comfortable
• Do not move someone with a potential spinal injury
• If the person is unconscious, check breathing and pulse
• Be prepared to provide CPR if you know how
• Gather important medical information (medications, allergies, conditions)

This is a serious situation that requires professional medical intervention immediately.
"""
        
        return HealthcareResponse(
            content=emergency_content,
            category='emergency',
            urgency_level='emergency',
            disclaimer=self.medical_disclaimer,
            emergency_guidance=self.emergency_guidance,
            follow_up_recommendations=['Call emergency services immediately'],
            sources=['Emergency medical protocols']
        )
    
    def _generate_fallback_response(self, query: str, category: str) -> str:
        """Generate fallback response when model is not available."""
        return f"""I understand you're asking about {category}-related health information.

While I don't have access to the full medical knowledge base right now, I can provide some general guidance:

For {category} questions:
1. Consult with qualified healthcare professionals
2. Use reputable medical resources and websites
3. Contact your doctor's office for specific concerns
4. For emergencies, call emergency services immediately

General health principles:
• Maintain a healthy lifestyle with good nutrition and exercise
• Stay hydrated and get adequate sleep
• Follow preventive care guidelines
• Take medications as prescribed
• Don't ignore persistent or severe symptoms

{self.medical_disclaimer}"""
    
    def _create_healthcare_response(self, content: str, query: str, category: str, urgency: str) -> HealthcareResponse:
        """Create structured healthcare response with safety measures."""
        # Determine emergency guidance if needed
        emergency_guidance = None
        if urgency in ['emergency', 'urgent']:
            emergency_guidance = self.emergency_guidance
        
        # Generate follow-up recommendations
        follow_up = self._generate_follow_up_recommendations(category, urgency)
        
        # Add sources
        sources = self._get_information_sources(category)
        
        # Ensure disclaimer is included
        full_content = content
        if self.disclaimer_required and self.medical_disclaimer not in content:
            full_content += f"\n\n{self.medical_disclaimer}"
        
        return HealthcareResponse(
            content=full_content,
            category=category,
            urgency_level=urgency,
            disclaimer=self.medical_disclaimer,
            emergency_guidance=emergency_guidance,
            follow_up_recommendations=follow_up,
            sources=sources
        )
    
    def _generate_follow_up_recommendations(self, category: str, urgency: str) -> List[str]:
        """Generate appropriate follow-up recommendations."""
        base_recommendations = {
            'emergency': [
                'Call emergency services immediately',
                'Do not delay seeking professional medical help',
                'Follow emergency protocols'
            ],
            'urgent': [
                'Contact your healthcare provider today',
                'Consider urgent care if doctor unavailable',
                'Monitor symptoms closely'
            ],
            'moderate': [
                'Schedule an appointment with your healthcare provider',
                'Monitor symptoms and note any changes',
                'Follow general health guidelines'
            ],
            'low': [
                'Discuss with your healthcare provider at your next visit',
                'Continue healthy lifestyle practices',
                'Stay informed about health topics'
            ]
        }
        
        category_specific = {
            'first_aid': [
                'Seek professional medical evaluation for serious injuries',
                'Keep first aid supplies updated',
                'Consider taking a first aid course'
            ],
            'preventive_care': [
                'Schedule regular health screenings',
                'Maintain healthy lifestyle habits',
                'Stay up to date with vaccinations'
            ],
            'symptoms': [
                'Keep a symptom diary',
                'Note any triggers or patterns',
                'Don\'t ignore persistent symptoms'
            ],
            'medication_info': [
                'Consult your pharmacist for medication questions',
                'Review medications with your doctor regularly',
                'Report any side effects to your healthcare provider'
            ]
        }
        
        recommendations = base_recommendations.get(urgency, [])
        recommendations.extend(category_specific.get(category, []))
        
        return recommendations
    
    def _get_information_sources(self, category: str) -> List[str]:
        """Get appropriate information sources for the category."""
        return [
            'Medical literature and evidence-based sources',
            'Healthcare professional guidelines',
            'Reputable medical organizations',
            'Peer-reviewed medical research'
        ]
    
    def _create_error_response(self, query: str) -> HealthcareResponse:
        """Create error response for failed healthcare queries."""
        return HealthcareResponse(
            content=f"I apologize, but I encountered an issue processing your health question. For any health concerns, please consult with qualified healthcare professionals.\n\n{self.medical_disclaimer}",
            category='general_health',
            urgency_level='moderate',
            disclaimer=self.medical_disclaimer,
            emergency_guidance=None,
            follow_up_recommendations=['Consult with healthcare professionals'],
            sources=['Professional medical consultation recommended']
        )
    
    def get_health_tips(self, category: str = 'general') -> Dict[str, Any]:
        """Provide general health and wellness tips."""
        tips_database = {
            'general': [
                'Maintain a balanced diet with fruits and vegetables',
                'Exercise regularly - at least 30 minutes most days',
                'Get 7-9 hours of quality sleep each night',
                'Stay hydrated by drinking plenty of water',
                'Practice stress management techniques',
                'Schedule regular health checkups'
            ],
            'nutrition': [
                'Eat a variety of colorful fruits and vegetables',
                'Choose whole grains over refined grains',
                'Include lean proteins in your diet',
                'Limit processed foods and added sugars',
                'Control portion sizes',
                'Read nutrition labels'
            ],
            'exercise': [
                'Start slowly and gradually increase intensity',
                'Include both cardio and strength training',
                'Find activities you enjoy',
                'Set realistic fitness goals',
                'Listen to your body and rest when needed',
                'Stay consistent with your routine'
            ],
            'mental_health': [
                'Practice mindfulness and meditation',
                'Maintain social connections',
                'Seek help when needed',
                'Limit exposure to negative news',
                'Engage in hobbies and activities you enjoy',
                'Practice gratitude daily'
            ]
        }
        
        tips = tips_database.get(category, tips_database['general'])
        
        return {
            'category': category,
            'tips': tips,
            'disclaimer': 'These are general wellness suggestions. Consult healthcare professionals for personalized advice.',
            'reminder': 'Individual health needs vary. Always consult with qualified healthcare providers.'
        }
    
    def get_first_aid_guide(self, situation: str) -> Dict[str, Any]:
        """Provide first aid guidance for common situations."""
        first_aid_guides = {
            'cuts_and_scrapes': {
                'steps': [
                    '1. Wash your hands thoroughly',
                    '2. Stop the bleeding by applying pressure with a clean cloth',
                    '3. Clean the wound gently with water',
                    '4. Apply antibiotic ointment if available',
                    '5. Cover with a sterile bandage',
                    '6. Change the bandage daily and keep the wound clean'
                ],
                'when_to_seek_help': [
                    'Deep cuts that won\'t stop bleeding',
                    'Signs of infection (redness, swelling, pus)',
                    'Cuts from dirty or rusty objects',
                    'If you haven\'t had a tetanus shot recently'
                ]
            },
            'burns': {
                'steps': [
                    '1. Remove from heat source immediately',
                    '2. Cool the burn with cool (not cold) water for 10-20 minutes',
                    '3. Remove jewelry or tight clothing from the burned area',
                    '4. Do not break blisters',
                    '5. Cover with a sterile, non-adhesive bandage',
                    '6. Take over-the-counter pain medication if needed'
                ],
                'when_to_seek_help': [
                    'Burns larger than the palm of your hand',
                    'Burns on face, hands, feet, or genitals',
                    'Third-degree burns (white or charred skin)',
                    'Burns from chemicals or electricity',
                    'Signs of infection'
                ]
            }
        }
        
        guide = first_aid_guides.get(situation)
        if guide:
            guide['disclaimer'] = self.medical_disclaimer
            guide['emergency_note'] = 'For serious injuries, call emergency services immediately'
        
        return guide or {'error': 'First aid guide not available for this situation'}
    
    def get_domain_stats(self) -> Dict[str, Any]:
        """Get healthcare domain statistics."""
        return {
            'domain': 'healthcare',
            'categories': self.categories,
            'safety_features': [
                'Medical disclaimers',
                'Emergency detection',
                'Urgency level assessment',
                'Professional referral guidance'
            ],
            'disclaimer_enabled': self.disclaimer_required,
            'emergency_redirect': self.emergency_redirect
        }
