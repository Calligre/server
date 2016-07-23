variable "aws_access_key" {}
variable "aws_secret_key" {}

variable "key_name" {}
variable "key_path" {}

variable "region" {
  default = "us-west-2"
}

variable "amis" {
  description = "Default Ubuntu 14.04 Server AMIs by region"
  default = {
    us-west-1 = "ami-049d8641"
    us-west-2 = "ami-9abea4fb"
    us-east-1 = "ami-a6b8e7ce"
  }
}
