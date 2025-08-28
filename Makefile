CONFIG?=bench/config.json
PROFILE?=savi_openai_62

.RECIPEPREFIX := >
.PHONY: setup bench report

setup:
>echo "No setup required"

bench:
>python -m bench.run --config $(CONFIG) --profile $(PROFILE)

report:
>python -m bench.report --config $(CONFIG)

serve:
>python -m http.server 8000
