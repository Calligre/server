resource "aws_instance" "conference" {
  tags {
    Name = "${var.name}"
  }

  instance_type = "${var.instance_type}"
  ami = "${var.ami}"

  connection {
    user = "ubuntu"
  }
  key_name = "${var.key_name}"

  vpc_security_group_ids = ["${aws_security_group.conference.id}"]
  subnet_id = "${aws_subnet.conference.id}"

  provisioner "file" {
    source = "../../api"
    destination = "/home/ubuntu"
  }

  provisioner "remote-exec" {
    script = "modules/conference/provision.sh"
  }
}

resource "aws_db_instance" "conference" {
  name                 = "${var.name}"

  allocated_storage    = 20
  engine               = "PostgreSQL"
  engine_version       = "9.5.2"
  instance_class       = "db.t2.micro"

  username             = "foo"
  password             = "bar"
  db_subnet_group_name = "${aws_vpc.conference.id}"
  parameter_group_name = "default.mysql5.6"
}
