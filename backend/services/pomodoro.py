def formatar_tempo(segundos):
    """Transforma segundos em formato MM:SS para o Timer do StudyUp."""
    minutos = segundos // 60
    secs = segundos % 60
    return f"{minutos:02d}:{secs:02d}"