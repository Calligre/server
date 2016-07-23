resource "aws_vpc" "alpha" {
  tags {
    Name = "alpha-demo"
  }
  cidr_block = "10.0.0.0/16"
}

resource "aws_internet_gateway" "alpha" {
  tags {
    Name = "alpha-demo"
  }
  vpc_id = "${aws_vpc.alpha.id}"
}

resource "aws_route" "internet_access" {
  route_table_id         = "${aws_vpc.alpha.main_route_table_id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.alpha.id}"
}

resource "aws_subnet" "alpha" {
  vpc_id                  = "${aws_vpc.alpha.id}"
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
}

resource "aws_security_group" "elb" {
  name   = "alpha-demo-elb"
  vpc_id = "${aws_vpc.alpha.id}"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "alpha" {
  name   = "alpha-demo"
  vpc_id = "${aws_vpc.alpha.id}"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

/*
resource "aws_elb" "alpha" {
  name = "alpha-demo"

  subnets         = ["${aws_subnet.alpha.id}"]
  security_groups = [
    "${aws_security_group.alpha.id}",
    "${aws_security_group.elb.id}"
  ]

  listener {
    instance_port     = 3000
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  listener {
    instance_port     = 3000
    instance_protocol = "http"
    lb_port           = 443
    lb_protocol       = "https"
    ssl_certificate_id = "arn:aws:acm:us-west-2:037954390517:certificate/ff174244-bc9d-4914-a05a-de1a86f8fc83"
  }

  health_check {
    healthy_threshold = 10
    unhealthy_threshold = 2
    timeout = 5
    target = "HTTP:3000/index.html"
    interval = 30
  }

  instances = ["${aws_instance.alpha.id}"]
}
*/
