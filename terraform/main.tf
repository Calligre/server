module "alpha-demo" {
  source = "./modules/alpha-demo"

  aws_access_key = "${var.aws_access_key}"
  aws_secret_key = "${var.aws_secret_key}"

  key_name = "${var.key_name}"
  key_path = "${var.key_path}"

  region = "${var.region}"
  ami = "${lookup(var.amis, var.region)}"
}
