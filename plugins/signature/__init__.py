from plugins.signature.signature import on_pre_llm_call, on_transform_llm_output


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("transform_llm_output", on_transform_llm_output)
