import re


class RegexGenerator:
    """Generates a regular expression that matches a set of example strings."""

    @staticmethod
    def generate(examples: list[str]) -> str:
        """
        Generate a refined regex pattern from a list of example strings.

        It attempts to identify common prefixes, suffixes, and numeric patterns
        to create a generalized regular expression.
        """
        if not examples:
            return ""

        # Filter and clean
        examples = [str(s).strip() for s in examples if s and str(s).strip()]
        if not examples:
            return ""

        # 1. If all strings are identical, return the escaped string
        if all(s == examples[0] for s in examples):
            return re.escape(examples[0])

        # 2. Try the 'number generalization' approach
        # Replace digits with \d+ in a template and see if it covers others
        template = examples[0]
        # We replace groups of digits
        digit_pattern = re.sub(r"\d+", r"\\d+", re.escape(template))

        try:
            compiled = re.compile(f"^{digit_pattern}$")
            # Match the raw example, not an escaped copy of it: escaping the candidate
            # shifts every character position against the pattern, so this branch could
            # never succeed and always fell through to the weaker prefix/suffix one.
            if all(compiled.match(s) for s in examples):
                return f"^{digit_pattern}$"
        except Exception:
            pass

        # 3. Common Prefix / Suffix approach
        prefix = RegexGenerator._get_common_prefix(examples)
        suffix = RegexGenerator._get_common_suffix(examples)

        # Escape them
        e_prefix = re.escape(prefix)
        e_suffix = re.escape(suffix)

        if prefix or suffix:
            # Re-check if prefix and suffix don't overlap the whole string
            if len(prefix) + len(suffix) < len(min(examples, key=len)):
                return f"^{e_prefix}.*?{e_suffix}$"
            else:
                return f"^{e_prefix}.*{e_suffix}$"

        # 4. Ultimate fallback
        return ".*"

    @staticmethod
    def _get_common_prefix(strs: list[str]) -> str:
        if not strs:
            return ""
        s1, s2 = min(strs), max(strs)
        for i, c in enumerate(s1):
            if i >= len(s2) or c != s2[i]:
                return s1[:i]
        return s1

    @staticmethod
    def _get_common_suffix(strs: list[str]) -> str:
        if not strs:
            return ""
        reversed_strs = [s[::-1] for s in strs]
        suffix = RegexGenerator._get_common_prefix(reversed_strs)
        return suffix[::-1]
