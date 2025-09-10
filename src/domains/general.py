"""
LocalMind General Domain

General-purpose AI assistance for queries outside specialized domains.
Provides helpful, accurate, and safe responses for a wide range of topics.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class GeneralResponse:
    """Structure for general domain responses."""
    content: str
    topic_category: str
    confidence_level: str
    related_topics: List[str]
    follow_up_suggestions: List[str]

class GeneralDomain:
    """
    General domain for LocalMind's broad-scope assistance.
    
    Features:
    - General knowledge and information
    - Problem-solving assistance
    - Creative and analytical thinking
    - Research and reference help
    - Writing and communication support
    - Technology and how-to guidance
    """
    
    def __init__(self, config: Dict[str, Any], model_engine=None, vector_db=None, conversation_memory=None):
        self.config = config
        self.model_engine = model_engine
        self.vector_db = vector_db
        self.conversation_memory = conversation_memory
        self.logger = logging.getLogger(__name__)
        
        # General domain configuration
        self.max_context_length = config['domains']['general']['max_context_length']
        
        # Topic categories for general queries
        self.topic_categories = self._initialize_topic_categories()
        
        # Response templates for different types of queries
        self.response_templates = self._initialize_response_templates()
        
        self.logger.info("GeneralDomain initialized")
    
    def _initialize_topic_categories(self) -> Dict[str, List[str]]:
        """Initialize topic categories for classification."""
        return {
            'technology': [
                'computer', 'software', 'internet', 'programming', 'app', 'digital',
                'phone', 'smartphone', 'technology', 'tech', 'device', 'gadget'
            ],
            'lifestyle': [
                'home', 'cooking', 'recipe', 'travel', 'hobby', 'entertainment',
                'movie', 'book', 'music', 'art', 'culture', 'fashion'
            ],
            'business': [
                'business', 'career', 'job', 'work', 'professional', 'interview',
                'resume', 'management', 'leadership', 'finance', 'money'
            ],
            'creative': [
                'creative', 'writing', 'story', 'art', 'design', 'music',
                'poetry', 'imagination', 'brainstorm', 'idea', 'innovative'
            ],
            'reference': [
                'fact', 'information', 'research', 'data', 'statistics',
                'definition', 'explanation', 'reference', 'lookup'
            ],
            'problem_solving': [
                'problem', 'solution', 'help', 'fix', 'solve', 'issue',
                'troubleshoot', 'advice', 'guidance', 'recommendation'
            ],
            'communication': [
                'write', 'letter', 'email', 'presentation', 'speech',
                'communication', 'language', 'translate', 'explain'
            ]
        }
    
    def _initialize_response_templates(self) -> Dict[str, str]:
        """Initialize response templates for different query types."""
        return {
            'technology': """I'll help you with this technology-related question. Let me provide 
            a clear explanation and practical guidance.""",
            
            'lifestyle': """I'm happy to help with your lifestyle question. I'll provide 
            helpful suggestions and practical advice.""",
            
            'business': """I'll assist you with this business-related query by providing 
            professional insights and actionable recommendations.""",
            
            'creative': """Let me help spark your creativity! I'll provide inspiration 
            and practical guidance for your creative endeavor.""",
            
            'reference': """I'll provide you with accurate information and helpful context 
            for your reference needs.""",
            
            'problem_solving': """Let me help you work through this problem systematically. 
            I'll break it down and suggest practical solutions.""",
            
            'communication': """I'll help you communicate effectively by providing guidance 
            on structure, tone, and clarity.""",
            
            'general': """I'll do my best to provide helpful information and guidance 
            for your question."""
        }
    
    def process_general_query(self, query: str, context: Optional[str] = None, 
                             language: str = 'en') -> GeneralResponse:
        """
        Process a general query with comprehensive assistance.
        
        Args:
            query: User's question or request
            context: Optional additional context
            language: Response language
            
        Returns:
            General response with helpful information
        """
        try:
            # Classify the topic category
            topic_category = self._classify_topic(query)
            
            # Get conversation context from memory
            conversation_context = []
            context_used = []
            if self.conversation_memory:
                conversation_context = self.conversation_memory.get_relevant_context(query)
                context_used = [ctx['content'][:100] + "..." for ctx in conversation_context[:3]]
            
            # Get relevant context from knowledge base
            knowledge_context = self._get_knowledge_context(query, topic_category)
            
            # Build comprehensive prompt with conversation context
            enhanced_prompt = self._build_general_prompt(
                query, topic_category, knowledge_context, context, conversation_context
            )
            
            # Generate response using model
            self.logger.debug(f"Model engine available: {self.model_engine is not None}")
            self.logger.debug(f"Model engine loaded: {self.model_engine.is_loaded if self.model_engine else False}")
            
            if self.model_engine and self.model_engine.is_loaded:
                response_content = self.model_engine.generate_response(enhanced_prompt)
                confidence_level = "high"
                self.logger.debug("Using model engine for response")
            else:
                response_content = self._generate_fallback_response(query, topic_category)
                confidence_level = "medium"
                self.logger.debug("Using fallback response")
            
            # Create structured response
            general_response = self._create_general_response(
                response_content, query, topic_category, confidence_level
            )
            
            # Store conversation in memory
            if self.conversation_memory:
                self.conversation_memory.add_conversation_turn(
                    user_message=query,
                    assistant_response=response_content,
                    domain='general',
                    confidence=confidence_level,
                    context_used=context_used
                )
            
            self.logger.debug(f"General query processed: {topic_category}")
            return general_response
            
        except Exception as e:
            self.logger.error(f"General query processing failed: {e}")
            return self._create_error_response(query)
    
    def _classify_topic(self, query: str) -> str:
        """Classify the query into a topic category."""
        query_lower = query.lower()
        
        # Score each category
        category_scores = {}
        for category, keywords in self.topic_categories.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            category_scores[category] = score
        
        # Return category with highest score, or 'general' if no clear match
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    def _get_knowledge_context(self, query: str, topic_category: str) -> str:
        """Retrieve relevant context from knowledge base."""
        if not self.vector_db:
            return ""
        
        try:
            # Search for relevant general knowledge
            results = self.vector_db.search_by_domain(query, 'general', k=3)
            
            # If no general domain results, search broadly
            if not results:
                results = self.vector_db.search(query, k=3)
            
            # Combine relevant content
            context_parts = []
            for result in results[:2]:  # Use top 2 results
                context_parts.append(result['document'])
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to get knowledge context: {e}")
            return ""
    
    def _build_general_prompt(self, query: str, topic_category: str, 
                             knowledge_context: str, user_context: Optional[str] = None,
                             conversation_context: List[Dict[str, Any]] = None) -> str:
        """Build comprehensive prompt for general queries with conversation memory."""
        # Get category-specific template
        template = self.response_templates.get(topic_category, self.response_templates['general'])
        
        # Build the prompt
        prompt_parts = [
            "You are LocalMind, a helpful and knowledgeable AI assistant operating completely offline.",
            "You have memory of previous conversations and can use context to provide better responses.",
            "Provide accurate, helpful, and comprehensive responses to user queries.",
            "",
            f"Topic Category: {topic_category}",
            f"Guidance: {template}",
            ""
        ]
        
        # Add conversation context if available
        if conversation_context:
            prompt_parts.extend([
                "Previous Conversation Context:",
                "Recent interactions and relevant past conversations:"
            ])
            for ctx in conversation_context[:3]:  # Use top 3 contexts
                prompt_parts.append(f"- {ctx['type']}: {ctx['content'][:200]}...")
            prompt_parts.append("")
        
        # Add knowledge context if available
        if knowledge_context:
            prompt_parts.extend([
                "Relevant Information:",
                knowledge_context,
                ""
            ])
        
        prompt_parts.extend([
            "Response Guidelines:",
            "• Be helpful, accurate, and informative",
            "• Use conversation context to provide personalized responses",
            "• Provide practical advice when appropriate",
            "• Break down complex topics into understandable parts",
            "• Suggest follow-up actions or related topics",
            "• Be concise but thorough",
            "• Use examples and analogies when helpful",
            "• Remember user preferences from past interactions"
        ])
        
        # Add user context if provided
        if user_context:
            prompt_parts.extend([
                "",
                "Additional Context:",
                user_context
            ])
        
        # Add the actual query
        prompt_parts.extend([
            "",
            f"User Question: {query}",
            "",
            "Provide a comprehensive and helpful response:"
        ])
        
        return '\n'.join(prompt_parts)
    
    def _generate_fallback_response(self, query: str, topic_category: str) -> str:
        """Generate fallback response when model is not available."""
        fallback_responses = {
            'technology': f"""I understand you're asking about {topic_category}. While I don't have 
access to the full knowledge base right now, here are some general suggestions:

1. Check official documentation or help resources
2. Look for tutorials or how-to guides
3. Consider reaching out to technical support
4. Try searching for similar issues and solutions
5. Break down the problem into smaller parts

For technology questions, it's often helpful to:
• Restart the device or application
• Check for updates
• Verify connections and settings
• Look for error messages or codes""",

            'problem_solving': f"""I'd like to help you solve this problem. Here's a systematic approach:

1. **Define the problem clearly**: What exactly is the issue?
2. **Gather information**: What do you already know?
3. **Brainstorm solutions**: What are possible approaches?
4. **Evaluate options**: Which solutions seem most promising?
5. **Take action**: Choose and implement a solution
6. **Review results**: Did it work? What can you learn?

Would you like to work through any of these steps together?""",

            'creative': f"""For creative projects, consider these approaches:

1. **Brainstorming**: Write down all ideas, even unusual ones
2. **Research**: Look at what others have done for inspiration
3. **Experimentation**: Try different approaches
4. **Iteration**: Refine and improve your ideas
5. **Feedback**: Share with others for input

Remember that creativity often comes from combining existing ideas in new ways!""",

            'general': f"""I'd be happy to help with your question. Here are some general approaches:

1. Break down complex questions into smaller parts
2. Consider different perspectives on the topic
3. Look for reliable sources of information
4. Think about practical applications
5. Consider both benefits and potential challenges

Is there a specific aspect you'd like to focus on?"""
        }
        
        return fallback_responses.get(topic_category, fallback_responses['general'])
    
    def _create_general_response(self, content: str, query: str, topic_category: str, confidence_level: str) -> GeneralResponse:
        """Create structured general response."""
        # Generate related topics
        related_topics = self._generate_related_topics(query, topic_category)
        
        # Generate follow-up suggestions
        follow_up_suggestions = self._generate_follow_up_suggestions(query, topic_category)
        
        return GeneralResponse(
            content=content,
            topic_category=topic_category,
            confidence_level=confidence_level,
            related_topics=related_topics,
            follow_up_suggestions=follow_up_suggestions
        )
    
    def _generate_related_topics(self, query: str, topic_category: str) -> List[str]:
        """Generate related topics for further exploration."""
        topic_relations = {
            'technology': ['software tools', 'troubleshooting', 'updates', 'security', 'best practices'],
            'lifestyle': ['tips and tricks', 'alternatives', 'budgeting', 'time management', 'resources'],
            'business': ['strategies', 'tools', 'networking', 'skills development', 'industry trends'],
            'creative': ['techniques', 'inspiration sources', 'tools and materials', 'skill building', 'sharing and feedback'],
            'reference': ['related facts', 'background information', 'sources', 'verification', 'updates'],
            'problem_solving': ['root causes', 'prevention', 'similar problems', 'tools and resources', 'expert advice'],
            'communication': ['audience considerations', 'tone and style', 'formatting', 'feedback', 'improvement'],
            'general': ['background information', 'related concepts', 'practical applications', 'further reading', 'expert opinions']
        }
        
        return topic_relations.get(topic_category, topic_relations['general'])
    
    def _generate_follow_up_suggestions(self, query: str, topic_category: str) -> List[str]:
        """Generate follow-up suggestions."""
        follow_up_templates = {
            'technology': [
                'Try the suggested solution and let me know the results',
                'Look up specific error messages if any occur',
                'Check for software updates',
                'Consider consulting technical documentation'
            ],
            'lifestyle': [
                'Start with small, manageable steps',
                'Research local resources and options',
                'Set realistic goals and timelines',
                'Track your progress'
            ],
            'business': [
                'Research industry best practices',
                'Network with professionals in the field',
                'Consider taking relevant courses',
                'Practice and refine your skills'
            ],
            'creative': [
                'Start with a small prototype or draft',
                'Gather feedback from others',
                'Experiment with different approaches',
                'Build a portfolio of your work'
            ],
            'reference': [
                'Verify information from multiple sources',
                'Check for recent updates',
                'Look for expert opinions',
                'Consider the context and limitations'
            ],
            'problem_solving': [
                'Test the solution in a controlled way',
                'Monitor the results',
                'Be prepared with backup plans',
                'Document what works'
            ],
            'communication': [
                'Practice your delivery',
                'Get feedback from others',
                'Adapt for your specific audience',
                'Refine based on responses'
            ],
            'general': [
                'Research the topic further',
                'Consider different perspectives',
                'Apply the information practically',
                'Share your findings with others'
            ]
        }
        
        return follow_up_templates.get(topic_category, follow_up_templates['general'])
    
    def _create_error_response(self, query: str) -> GeneralResponse:
        """Create error response for failed queries."""
        return GeneralResponse(
            content="I apologize, but I encountered an issue processing your question. Please try rephrasing your question or breaking it into smaller parts. I'm here to help with a wide range of topics!",
            topic_category='general',
            confidence_level='low',
            related_topics=['question clarification', 'alternative approaches'],
            follow_up_suggestions=['Rephrase your question', 'Break into smaller parts', 'Provide more context']
        )
    
    def provide_writing_assistance(self, writing_type: str, topic: str, requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provide specialized writing assistance."""
        writing_guides = {
            'email': {
                'structure': ['Subject line', 'Greeting', 'Main content', 'Closing', 'Signature'],
                'tips': [
                    'Be clear and concise in your subject line',
                    'Use a professional greeting',
                    'Get to the point quickly',
                    'Use bullet points for lists',
                    'Proofread before sending'
                ]
            },
            'essay': {
                'structure': ['Introduction', 'Body paragraphs', 'Conclusion'],
                'tips': [
                    'Start with a strong thesis statement',
                    'Support arguments with evidence',
                    'Use transitions between paragraphs',
                    'Conclude by reinforcing your main points',
                    'Cite sources appropriately'
                ]
            },
            'letter': {
                'structure': ['Date', 'Address', 'Greeting', 'Body', 'Closing', 'Signature'],
                'tips': [
                    'Use appropriate formal or informal tone',
                    'Be clear about your purpose',
                    'Organize thoughts logically',
                    'End with a clear call to action if needed',
                    'Review for tone and clarity'
                ]
            }
        }
        
        guide = writing_guides.get(writing_type, {
            'structure': ['Introduction', 'Main content', 'Conclusion'],
            'tips': ['Be clear and organized', 'Consider your audience', 'Review and revise']
        })
        
        return {
            'writing_type': writing_type,
            'topic': topic,
            'structure': guide['structure'],
            'tips': guide['tips'],
            'requirements': requirements or {}
        }
    
    def provide_research_guidance(self, research_topic: str, purpose: str = 'general') -> Dict[str, Any]:
        """Provide research guidance and methodology."""
        return {
            'topic': research_topic,
            'purpose': purpose,
            'research_steps': [
                '1. Define your research question clearly',
                '2. Identify key terms and concepts',
                '3. Find reliable sources of information',
                '4. Evaluate source credibility and bias',
                '5. Take organized notes',
                '6. Synthesize information from multiple sources',
                '7. Draw conclusions based on evidence'
            ],
            'source_types': [
                'Academic journals and papers',
                'Books by experts in the field',
                'Government and institutional reports',
                'Reputable news sources',
                'Professional organization websites'
            ],
            'evaluation_criteria': [
                'Author credentials and expertise',
                'Publication date and relevance',
                'Source reputation and peer review',
                'Evidence and documentation quality',
                'Potential bias or conflicts of interest'
            ]
        }
    
    def get_domain_stats(self) -> Dict[str, Any]:
        """Get general domain statistics."""
        return {
            'domain': 'general',
            'topic_categories': list(self.topic_categories.keys()),
            'features': [
                'General knowledge assistance',
                'Problem-solving guidance',
                'Writing and communication support',
                'Research methodology',
                'Creative assistance',
                'Technology help'
            ],
            'max_context_length': self.max_context_length
        }
