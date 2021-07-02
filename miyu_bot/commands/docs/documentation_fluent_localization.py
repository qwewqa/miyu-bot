from fluent.runtime import FluentLocalization


class DocumentationFluentLocalization(FluentLocalization):
    def format_value(self, msg_id, args=None, fallback=None):
        for bundle in self._bundles():
            if not bundle.has_message(msg_id):
                continue
            msg = bundle.get_message(msg_id)
            if not msg.value:
                continue
            val, errors = bundle.format_pattern(msg.value, args)
            return val
        return fallback if fallback is not None else msg_id
