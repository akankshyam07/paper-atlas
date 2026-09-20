"""Deepgram speech provider (Deepgram challenge). Implements SpeechProvider.

Isolates the Deepgram SDK here. Optional voice layer: transcribe mic audio for
the canvas chat bar, synthesize AI explanations for read-aloud. Never on the
core research path.
"""
# TODO: pip install deepgram-sdk; DEEPGRAM_API_KEY; transcribe() via
# listen.prerecorded / live, synthesize() via speak. Wire into chat input + a
# read-aloud button on AI_SUMMARY nodes.
