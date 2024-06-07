import requests
import yaml


class ResponseError(ValueError):
    pass


class Planetside:
    def __init__(self, service_id: str) -> None:
        self.sid = service_id

    @property
    def get_base(self):
        return f"https://census.daybreakgames.com/{self.sid}/get/ps2:v2/"

    def get(self, collection: str) -> requests.Response | ResponseError:
        compelte_request = f"{self.get_base}{collection}"
        result = requests.api.get(compelte_request)
        if result.status_code == 200:
            return result
        else:
            raise ResponseError(f"The request {collection} returned a non-200 status")


def init_planetside():
    with open(".credentials.yaml", "r") as f:
        credentials = yaml.safe_load(f)
    planetside = Planetside(service_id=credentials["planetside"]["service_id"])
    return planetside


def main():
    planetside = init_planetside()
    cid = planetside.get(collection="character/?name.first=LordMcze")
    print(cid.json())


if __name__ == "__main__":
    main()
