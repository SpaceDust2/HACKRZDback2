from django.db import models


class Train(models.Model):
    id = models.AutoField(primary_key=True)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    date = models.CharField(max_length=100)

    def to_dict(self):
        return {
            'id': self.id,
            'origin': self.origin,
            'destination': self.destination,
            'date': self.date
        }


class Stop(models.Model):
    id = models.AutoField(primary_key=True)
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    stop_number = models.IntegerField()
    stop_name = models.CharField(max_length=100)
    arrival_time = models.CharField(max_length=100)
    stop_duration = models.CharField(max_length=100)
    departure_time = models.CharField(max_length=100)

    def to_dict(self):
        return {
            'id': self.id,
            'train_id': self.train_id,
            'stop_number': self.stop_number,
            'stop_name': self.stop_name,
            'arrival_time': self.arrival_time,
            'stop_duration': self.stop_duration,
            'departure_time': self.departure_time
        }


class Purchase(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_time = models.CharField(max_length=100)

    def to_dict(self):
        return {
            'id': self.id,
            'purchase_time': self.purchase_time
        }
