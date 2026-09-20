"""Token Company inference optimizer (Token Company challenge: LLM cost saving).
Implements InferenceOptimizationProvider.

Challenge = save as much as possible on the LLM stack: cheaper-model routing,
caching, smaller inputs / denser outputs, prompt compression. SDK/endpoint
isolated here; the app calls registry.get_inference_optimizer().optimize(...)
around every LLM call and never sees the vendor.
"""
# TODO: response cache (hash prompt -> completion); route cheap vs strong model
# by task; compress long context (their models at thetokencompany.com). Measure
# tokens saved — that measurement is the challenge deliverable.
