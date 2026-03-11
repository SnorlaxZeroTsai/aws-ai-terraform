"""
RAG Prompt Templates
Provides prompt templates for RAG-based question answering
"""

from typing import List, Dict, Any


class RAGPrompts:
    """Prompt templates for RAG systems"""

    @staticmethod
    def get_qa_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a Q&A prompt with retrieved context

        Args:
            query: User query
            context_chunks: Retrieved context chunks

        Returns:
            Formatted prompt
        """
        # Format context
        context_text = RAGPrompts._format_context(context_chunks)

        prompt = f"""You are a helpful AI assistant that answers questions based on the provided context. Use the context below to answer the user's question accurately and concisely.

Context:
{context_text}

Question: {query}

Instructions:
1. Answer the question using ONLY the information provided in the context
2. If the context doesn't contain enough information to answer the question, say "I don't have enough information to answer this question."
3. Be concise and direct in your response
4. If relevant, cite specific parts of the context that support your answer

Answer:"""

        return prompt

    @staticmethod
    def get_summary_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a summarization prompt with retrieved context

        Args:
            query: User query
            context_chunks: Retrieved context chunks

        Returns:
            Formatted prompt
        """
        context_text = RAGPrompts._format_context(context_chunks)

        prompt = f"""Based on the provided context, summarize the information relevant to the user's query.

Context:
{context_text}

Query: {query}

Instructions:
1. Provide a concise summary of the information in the context that's relevant to the query
2. Focus on key points and main ideas
3. Keep the summary brief but comprehensive
4. Use bullet points if multiple key points exist

Summary:"""

        return prompt

    @staticmethod
    def get_explanation_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate an explanation prompt with retrieved context

        Args:
            query: User query
            context_chunks: Retrieved context chunks

        Returns:
            Formatted prompt
        """
        context_text = RAGPrompts._format_context(context_chunks)

        prompt = f"""You are a knowledgeable tutor. Explain the concept or answer the question using the provided context. Make your explanation clear and easy to understand.

Context:
{context_text}

Question: {query}

Instructions:
1. Provide a clear, step-by-step explanation
2. Use simple language and analogies if helpful
3. Break down complex ideas into understandable parts
4. If the context contains examples, use them to illustrate your explanation

Explanation:"""

        return prompt

    @staticmethod
    def _format_context(chunks: List[Dict[str, Any]]) -> str:
        """
        Format context chunks into a single string

        Args:
            chunks: List of context chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No context available."

        formatted_chunks = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', '')
            score = chunk.get('score', 0)
            formatted_chunks.append(
                f"[Source {i}] (Relevance: {score:.2f})\n{content}"
            )

        return '\n\n---\n\n'.join(formatted_chunks)

    @staticmethod
    def get_system_prompt() -> str:
        """
        Get the system prompt for the RAG assistant

        Returns:
            System prompt
        """
        return """You are a helpful AI assistant powered by a knowledge base. You answer questions by retrieving relevant information from the knowledge base and using it to provide accurate, context-aware responses.

Your capabilities:
- Answering questions using retrieved knowledge
- Summarizing information from multiple sources
- Explaining concepts based on provided context
- Admitting when information is insufficient

Your guidelines:
- Always base your answers on the provided context
- Be concise and direct
- Cite sources when relevant
- If the context doesn't contain the answer, say so clearly
- Maintain a helpful, professional tone"""

    @staticmethod
    def get_conversational_prompt(query: str, context_chunks: List[Dict[str, Any]],
                                 conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Generate a conversational prompt with context and history

        Args:
            query: User query
            context_chunks: Retrieved context chunks
            conversation_history: Previous conversation turns

        Returns:
            Formatted prompt
        """
        context_text = RAGPrompts._format_context(context_chunks)

        # Add conversation history
        history_text = ""
        if conversation_history:
            history_text = "\nConversation History:\n"
            for turn in conversation_history[-3:]:  # Last 3 turns
                role = turn.get('role', 'user')
                content = turn.get('content', '')
                history_text += f"{role.capitalize()}: {content}\n"
            history_text += "\n"

        prompt = f"""You are a helpful AI assistant having a conversation with a user. Use the provided context and conversation history to give natural, context-aware responses.

{history_text}Context:
{context_text}

Current User Question: {query}

Instructions:
1. Respond naturally to the user's current question
2. Use the context and conversation history as appropriate
3. Be conversational but accurate
4. If referring to previous parts of the conversation, be clear about it
5. Keep responses concise and relevant

Response:"""

        return prompt


class PromptBuilder:
    """Builder for constructing RAG prompts"""

    def __init__(self, template_type: str = 'qa'):
        """
        Initialize the prompt builder

        Args:
            template_type: Type of prompt template ('qa', 'summary', 'explanation', 'conversational')
        """
        self.template_type = template_type
        self.system_prompt = RAGPrompts.get_system_prompt()

    def build(self, query: str, context_chunks: List[Dict[str, Any]],
             conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Build a complete prompt

        Args:
            query: User query
            context_chunks: Retrieved context chunks
            conversation_history: Optional conversation history

        Returns:
            Complete prompt
        """
        if self.template_type == 'qa':
            return RAGPrompts.get_qa_prompt(query, context_chunks)
        elif self.template_type == 'summary':
            return RAGPrompts.get_summary_prompt(query, context_chunks)
        elif self.template_type == 'explanation':
            return RAGPrompts.get_explanation_prompt(query, context_chunks)
        elif self.template_type == 'conversational':
            return RAGPrompts.get_conversational_prompt(
                query, context_chunks, conversation_history
            )
        else:
            raise ValueError(f"Unknown template type: {self.template_type}")

    def set_template(self, template_type: str) -> None:
        """
        Change the template type

        Args:
            template_type: New template type
        """
        self.template_type = template_type
