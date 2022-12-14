# Generated by Django 3.1 on 2023-01-10 03:31

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import edm_calibration.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('instruments', '0001_initial'),
        ('baseline_calibration', '0001_initial'),
        ('calibrationsites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='uPillar_Survey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auto_base_calibration', models.BooleanField(default=True)),
                ('survey_date', models.DateField()),
                ('computation_date', models.DateField()),
                ('observer', models.CharField(blank=True, max_length=25, null=True)),
                ('weather', models.CharField(choices=[('Sunny/Clear', 'Sunny/Clear'), ('Partially cloudy', 'Partially cloudy'), ('Cloudy', 'Cloudy'), ('Overcast', 'Overcast'), ('Drizzle', 'Drizzle'), ('Raining', 'Raining'), ('Stormy', 'Stormy')], help_text='Weather conditions', max_length=25)),
                ('job_number', models.CharField(help_text='Job reference eg., JN 20212216', max_length=25)),
                ('mets_applied', models.BooleanField(default=True, help_text='Meterological corrections have been applied in the EDM instrument.', verbose_name='Atmospheric corrections applied to EDM data')),
                ('thermo_calib_applied', models.BooleanField(default=True, help_text='The thermometer calibration correction has been applied prior to data import.', verbose_name='thermometer calibration corrections applied')),
                ('baro_calib_applied', models.BooleanField(default=True, help_text='The barometer calibration correction has been applied prior to data import.', verbose_name='barometer calibration corrections applied')),
                ('hygro_calib_applied', models.BooleanField(default=True, help_text='The hygrometer correction has been applied prior to data import.', verbose_name='Hygrometer calibration corrections applied')),
                ('scalar', models.DecimalField(decimal_places=2, default=1.0, help_text='a-priori standard uncertainties are multiplied by the a-priori scalar', max_digits=6, verbose_name='a-priori scalar')),
                ('outlier_criterion', models.DecimalField(decimal_places=1, default=2, help_text='Number of standard deviations for outlier detection threashold.', max_digits=2, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('test_cyclic', models.BooleanField(default=False, help_text="Test Instrument For Cyclic Errors (Nb. Instrument Parameters Require 'Unit Lenght'", verbose_name='Test for cyclic errors')),
                ('fieldnotes_upload', models.FileField(blank=True, null=True, upload_to=edm_calibration.models.get_upload_to_location, verbose_name='Scanned fieldnotes')),
                ('variance', models.FloatField(blank=True, help_text='Variance of least squares adjustment of the calibration', null=True)),
                ('degrees_of_freedom', models.IntegerField(blank=True, help_text='Degrees of freedom of calibration', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(500)])),
                ('k', models.FloatField(blank=True, null=True, verbose_name='coverage factor')),
                ('uploaded_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('barometer', models.ForeignKey(help_text='Barometer used for survey', limit_choices_to={'mets_specs__mets_model__inst_type': 'baro'}, on_delete=django.db.models.deletion.PROTECT, related_name='ufield_barometer', to='instruments.mets_inst')),
                ('calibrated_baseline', models.ForeignKey(help_text='Baseline certified distances', null=True, on_delete=django.db.models.deletion.PROTECT, to='baseline_calibration.pillar_survey')),
                ('edm', models.ForeignKey(help_text='EDM used for survey', on_delete=django.db.models.deletion.PROTECT, to='instruments.edm_inst')),
                ('hygrometer', models.ForeignKey(blank=True, help_text='Hygrometer, if used for survey', limit_choices_to={'mets_specs__mets_model__inst_type': 'hygro'}, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ufield_hygrometer', to='instruments.mets_inst')),
                ('prism', models.ForeignKey(help_text='Prism used for survey', on_delete=django.db.models.deletion.PROTECT, to='instruments.prism_inst')),
                ('site', models.ForeignKey(help_text='Baseline certified distances', null=True, on_delete=django.db.models.deletion.PROTECT, to='calibrationsites.calibrationsite')),
                ('thermometer', models.ForeignKey(help_text='Thermometer used for survey', limit_choices_to={'mets_specs__mets_model__inst_type': 'thermo'}, on_delete=django.db.models.deletion.PROTECT, related_name='ufield_thermometer', to='instruments.mets_inst')),
                ('uncertainty_budget', models.ForeignKey(help_text='Preset uncertainty budget', on_delete=django.db.models.deletion.PROTECT, to='baseline_calibration.uncertainty_budget')),
            ],
            options={
                'ordering': ['edm', 'survey_date'],
            },
        ),
        migrations.CreateModel(
            name='uEDM_Observation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inst_ht', models.DecimalField(decimal_places=3, max_digits=4, verbose_name='Instrument height')),
                ('tgt_ht', models.DecimalField(decimal_places=3, max_digits=4, verbose_name='Target height')),
                ('raw_slope_dist', models.DecimalField(decimal_places=5, max_digits=9, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1000)], verbose_name='slope distance')),
                ('raw_temperature', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(50.0)])),
                ('raw_pressure', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1500.0)])),
                ('raw_humidity', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100.0)])),
                ('use_for_distance', models.BooleanField(default=True, help_text='This observation (will) / (will not) be used for determining the calibration of the edmi.', verbose_name='Use for surveying the certified distances')),
                ('from_pillar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calibrationsites.pillar')),
                ('pillar_survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='edm_calibration.upillar_survey')),
                ('to_pillar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='calibrationsites.pillar')),
            ],
            options={
                'ordering': ['pillar_survey', 'from_pillar', 'to_pillar'],
            },
        ),
        migrations.CreateModel(
            name='uCalibration_Parameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(choices=[('zpc', 'zero point correction'), ('scf', 'scale correction factor'), ('1C', '1 - Cyclic'), ('2C', '2 - Cyclic'), ('3C', '3 - Cyclic'), ('4C', '4 - Cyclic')], max_length=3)),
                ('value', models.FloatField(verbose_name='parameter Value')),
                ('standard_deviation', models.FloatField(verbose_name='standard deviation of this parameter')),
                ('pillar_survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='edm_calibration.upillar_survey')),
            ],
            options={
                'ordering': ['pillar_survey', 'term'],
            },
        ),
        migrations.AddConstraint(
            model_name='upillar_survey',
            constraint=models.CheckConstraint(check=models.Q(('site__isnull', False), ('calibrated_baseline__isnull', False), _connector='OR'), name='Both site and calibrated basline fields can not be null'),
        ),
        migrations.AlterUniqueTogether(
            name='ucalibration_parameter',
            unique_together={('pillar_survey', 'term')},
        ),
    ]
