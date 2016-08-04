provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"

  region = "${var.region}"
}


module "common" {
  source = "./modules/common"

  key_name = "${var.key_name}"
  key_path = "${var.key_path}"
}

module "alpha-demo" {
  source = "./modules/alpha-demo"

  key_name = "${var.key_name}"
  ami = "${lookup(var.amis, var.region)}"
}

module "conference" {
  source = "./modules/conference"

  name = "test-conference"
  key_name = "${var.key_name}"
  ami = "${lookup(var.amis, var.region)}"
}
