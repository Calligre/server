resource "aws_instance" "alpha" {
  tags {
    Name = "alpha-demo"
  }

  instance_type = "${var.instance_type}"
  ami = "${var.ami}"

  connection {
    user = "ubuntu"
  }
  key_name = "${var.key_name}"

  vpc_security_group_ids = ["${aws_security_group.alpha.id}"]
  subnet_id = "${aws_subnet.alpha.id}"

  provisioner "file" {
    source = "../../../alpha"
    destination = "/home/ubuntu"
  }

  provisioner "remote-exec" {
    script = "modules/alpha-demo/provision.sh"
  }
}
