from typing import BinaryIO, Sequence

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

    def query_manual(self, pdf_streams: Sequence[BinaryIO], user_query: str) -> str:
        """
        Envia os bytes de um ou mais PDFs diretamente no contexto da requisição
        junto com a dúvida técnica do operador.
        """
        parts = []
        for pdf_stream in pdf_streams:
            # Garante leitura dos bytes a partir do início
            pdf_stream.seek(0)
            parts.append(
                types.Part.from_bytes(data=pdf_stream.read(), mime_type="application/pdf")
            )

        system_instruction = (
            "Você é um engenheiro sênior especialista em processos de manufatura eletrônica SMT. "
            "Sua tarefa é responder à dúvida técnica do operador baseando-se estritamente nas informações "
            "e procedimentos contidos nos manuais técnicos em anexo. Se houver mais de um manual, indique "
            "de qual documento a informação foi extraída sempre que possível. Seja direto, prático e cite "
            "as seções ou parâmetros dos manuais sempre que disponíveis. Se a informação não constar nos "
            "documentos, declare explicitamente que os manuais não contemplam essa instrução."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                *parts,
                f"{system_instruction}\n\nPergunta técnica do operador: {user_query}",
            ]
        )

        return response.text
