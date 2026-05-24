from plugins.signature.signature import (
    on_pre_llm_call,
    on_post_api_request,
    on_post_tool_call,
    on_transform_llm_output,
)


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("post_api_request", on_post_api_request)
    ctx.register_hook("post_tool_call", on_post_tool_call)
    ctx.register_hook("transform_llm_output", on_transform_llm_output)
