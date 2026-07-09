def retokenize(request):
    # per-request re-tokenization — the uncached bottleneck
    return request.text.lower().split()
