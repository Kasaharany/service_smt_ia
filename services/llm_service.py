from typing import BinaryIO
from google import genai
from google.genai import types

from config.settings import DEFAULT_GEMINI_MODEL


class TechnicalManualAssistant:
    """
    Serviço de consulta técnica a manuais confidenciais via LLM.
    Processamento estritamente em memória volátil, sem persistência em disco.
    """

    def __init__(self, api_key: str, model_name: str = DEFAULT_GEMINI_MODEL):
        if not api_key:
            raise ValueError("Chave de API do Gemini não informada.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def query_manual(self, pdf_stream: BinaryIO, user_query: str) -> str:
        """
        Envia os bytes do PDF diretamente no contexto da requisição
        junto com a dúvida técnica do operador.
        """
        # Garante leitura dos bytes a partir do início
        pdf_stream.seek(0)
        pdf_bytes = pdf_stream.read()

        system_instruction = (
            "Você é um engenheiro sênior especialista em processos de manufatura eletrônica SMT. "
            "Sua tarefa é responder à dúvida técnica do operador baseando-se estritamente nas informações "
            "e procedimentos contidos no manual técnico em anexo. Seja direto, prático e cite as seções "
            "ou parâmetros do manual sempre que disponíveis. Se a informação não constar no documento, "
            "declare explicitamente que o manual não contempla essa instrução."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                f"{system_instruction}\n\nPergunta técnica do operador: {user_query}"
            ]
        )

        return response.text
