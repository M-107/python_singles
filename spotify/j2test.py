from pathlib import Path

import jinja2


def jinja2_render(input_file: str, output_file: str, data: dict):
    input_path = Path(input_file)
    input_dir = (input_path.parent).resolve()
    if input_path.exists():
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath=str(input_dir))
        )
        template = env.get_template(name=input_file)
        rendered = template.render(data)
        out_file = Path(output_file)
        with out_file.open("w", encoding="utf-8") as of:
            of.write(rendered)


def main():
    template_path = "j2template.jinja"
    output_path = "j2resolved.yaml"
    data = {"var_version": "3.11.4", "var_path": str(Path.home().resolve())}
    jinja2_render(input_file=template_path, output_file=output_path, data=data)


if __name__ == "__main__":
    main()
