variable "aws_access_key" {}
variable "aws_secret_key" {}

variable "key_name" {}
variable "key_path" {}

variable "region" {}

variable "ami" {}
variable "instance_type" {
  default = "t2.micro"
}
